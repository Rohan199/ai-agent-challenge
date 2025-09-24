import pandas as pd 
import pytest
from pathlib import Path

from custom_parsers.icici_parser import parse

TARGET_BANK = "icici"


def test_parser_output_matches_csv():
    """
    Validates that the agent-generated parser's output DataFrame
    is identical to the ground-truth CSV.
    """
    print(f"--- Validating parser for {TARGET_BANK} ---")
    
    # Define paths
    base_path = Path('data') / TARGET_BANK
    pdf_path = base_path / f'{TARGET_BANK} sample.pdf'
    csv_path = base_path / f'result.csv'

    # Check if parser and data exist
    assert pdf_path.exists(), "PDF sample file not found."
    assert csv_path.exists(), "CSV sample file not found."
    
    # 1. Load the expected DataFrame from the CSV
    try:
        expected_df = pd.read_csv(csv_path, dayfirst=True, parse_dates=['Date'])
        print("Successfully loaded expected data from CSV.")
    except Exception as e:
        pytest.fail(f"Failed to read the ground-truth CSV: {e}")

    # 2. Run the agent-generated parser to get the result
    try:
        result_df = parse(str(pdf_path))
        print("Successfully executed the agent-generated parser.")
    except Exception as e:
        pytest.fail(f"The agent's parse() function threw an exception: {e}")

    # 3. Normalize both DataFrames for a reliable comparison
    expected_df = expected_df.reset_index(drop=True).reindex(sorted(expected_df.columns), axis=1)
    result_df = result_df.reset_index(drop=True).reindex(sorted(result_df.columns), axis=1)
    
    # 4. Assert equality
    try:
        pd.testing.assert_frame_equal(result_df, expected_df)
        print("✅ SUCCESS: DataFrames match perfectly!")
    except AssertionError as e:
        print("❌ FAILURE: DataFrames do not match.")
        # pytest.fail will automatically capture and display the detailed diff
        pytest.fail(f"DataFrame comparison failed: {e}", pytrace=False)
