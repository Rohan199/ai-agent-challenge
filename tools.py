import json
import os
import subprocess
import pandas as pd 
import pdfplumber
from langchain.tools import tool
from pathlib import Path

@tool
def analyze_pdf_structure(pdf_path: str) -> str:
    """
    Analyzes the first 3 pages of a PDF file to understand its structure.
    Extracts text content and information about any detected tables.
    This is the first step to inform the parser generation.
    Returns a JSON string of the analysis.
    """
    print(f"Analyzing PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        return f"Error: PDF file not found at {pdf_path}"
    try:
        with pdfplumber.open(pdf_path) as pdf:
            analysis = {
                "text_sample": "\n".join(page.extract_text() for page in pdf.pages[:3]),
                "table_info": [
                    f"Page {i+1} tables: {len(page.extract_tables())}"
                    for i, page in enumerate(pdf.pages[:3])
                ],
                "total_pages": len(pdf.pages),
            }
        print("PDF analysis complete.")
        return json.dumps(analysis, indent=2)
    except Exception as e:
        print(f"PDF analysis failed: {e}")
        return f"Error analyzing PDF: {e}"

@tool
def test_parser_in_docker(generated_parser_code: str, target_bank: str) -> str:
    """
    Tests the generated Python parser code safely by executing it inside a Docker container.
    It compares the output DataFrame to the expected CSV. 
    Returns a success message or a detailed error and diff report.
    """
    print("Testing parser in a Docker container...")
    temp_dir = "temp_test_artifacts"
    os.makedirs(temp_dir, exist_ok=True)

    parser_file = os.path.join(temp_dir, "parser_to_test.py")   # Parser script 
    runner_file = os.path.join(temp_dir, "test_runner.py")      # Runner script

    with open(parser_file, "w") as f:
        f.write(generated_parser_code)

    runner_script = f"""
import sys
import pandas as pd
import traceback
from pathlib import Path
from parser_to_test import parse

def main(target_bank: str):
    try:
        # Use pathlib to construct paths correctly inside the container
        base_path = Path('/app/data') / target_bank
        pdf_path = base_path / f'{{target_bank}} sample.pdf'
        csv_path = base_path / f'{{target_bank}}_sample.csv'
        
        # Pass the string representation of the path to the parser
        result_df = parse(str(pdf_path))
        expected_df = pd.read_csv(str(csv_path), parse_dates=True, infer_datetime_format=True)
        
        # ... (rest of the runner script is identical) ...

    except Exception as e:
        print(f"FAILURE: An exception occurred during testing.\\n{{traceback.format_exc()}}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_runner.py <target_bank>")
        sys.exit(1)
    target_bank_arg = sys.argv[1]
    main(target_bank_arg)
    """
    with open(runner_file, "w") as f:
        f.write(runner_script)

    try:
        # Construct the Docker command to run the test in isolation 
        command = ["docker", "run", "--rm",
                    # Mount the runner, parser, and data into the container
                   "-v", f"{os.path.abspath(runner_file)}:/app/test_runner.py:ro",
                   "-v", f"{os.path.abspath(parser_file)}:/app/parser_to_test.py:ro",
                   "-v", f"{os.path.abspath('data')}:/app/data:ro",
                   "parser-agent",  # Use the same image we are already running in
                   "python", "test_runner.py"
        ]

        proc = subprocess.run(command, capture_output=True, text=True, timeout=60)

        if proc.returncode == 0 and "SUCCESS" in proc.stdout:
            print("Test passed successfully.")
            return proc.stdout
        else:
            print("Test failed.")
            # Combine stdout and stderr for a complete error report for the LLM
            return f"Test Failed! Output:\\n{proc.stdout}\\nStderr:\\n{proc.stderr}"

    except subprocess.TimeoutExpired:
        return f"Test Failed: The test script took too long to execute (possibly infinite loop)."
    except Exception as e:
        return f"Test Failed: An error occurred setting up the test environment: {e}"

@tool   
def save_parser_to_file(final_parser_code: str, target_bank: str) -> str:
    """
    Saves the final, validated Python parser code to a file in the 
    'custom_parsers' directory. Should only be called after tests have passed.
    """
    print("Saving the final parser for {target_bank}...")
    try:
        parser_path = os.path.join("custom_parsers", f"{target_bank}_parser.py")
        with open(parser_path, "w") as f:
            f.write(final_parser_code)
        print(f"Parser saved to {parser_path}")
        return f"successfully saved parser to {parser_path}"
    except Exception as e:
        return f"Error saving file: {e}"
