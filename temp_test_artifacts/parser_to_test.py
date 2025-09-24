
import pandas as pd
import pdfplumber

def parse(pdf_path: str) -> pd.DataFrame:
    """
    Parses an ICICI bank statement PDF and returns a pandas DataFrame.

    This version uses pdfplumber's table extraction capabilities for better accuracy.

    Args:
        pdf_path (str): The file path to the PDF bank statement.

    Returns:
        pd.DataFrame: A DataFrame containing the transaction data with columns:
                      'Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'.
    """
    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # extract_tables() returns a list of tables on the page
            tables = page.extract_tables()
            if tables:
                # Assuming the first table on the page is the transaction table
                all_tables.extend(tables[0])

    if not all_tables:
        return pd.DataFrame()

    # The first row of the first table is the header
    header = all_tables[0]
    # All subsequent rows are data
    data = all_tables[1:]

    # Create DataFrame
    df = pd.DataFrame(data, columns=header)
    
    # --- Data Cleaning and Validation ---
    
    # Drop rows where 'Date' is None or empty, which are likely footers or artifacts
    df = df.dropna(subset=['Date'])
    df = df[df['Date'] != '']

    # Rename columns to a standard format
    df.columns = ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']

    # --- Data Type Conversion ---

    # Convert Date to datetime objects
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')

    # Clean and convert numeric columns
    for col in ['Debit Amt', 'Credit Amt', 'Balance']:
        # Replace empty strings or None with '0'
        df[col] = df[col].fillna('0').replace('', '0')
        # Remove commas
        df[col] = df[col].str.replace(',', '')
        # Convert to numeric, coercing errors
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df
