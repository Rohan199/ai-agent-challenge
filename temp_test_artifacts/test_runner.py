
import sys
import pandas as pd
import traceback
from pathlib import Path
from parser_to_test import parse

def main(target_bank: str):
    try:
        # Use pathlib to construct paths correctly inside the container
        base_path = Path('/app/data') / target_bank
        pdf_path = base_path / f'{target_bank} sample.pdf'
        csv_path = base_path / f'{target_bank}_sample.csv'
        
        # Pass the string representation of the path to the parser
        result_df = parse(str(pdf_path))
        expected_df = pd.read_csv(str(csv_path), parse_dates=True, infer_datetime_format=True)
        
        # ... (rest of the runner script is identical) ...

    except Exception as e:
        print(f"FAILURE: An exception occurred during testing.\n{traceback.format_exc()}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_runner.py <target_bank>")
        sys.exit(1)
    target_bank_arg = sys.argv[1]
    main(target_bank_arg)
    