import pandas as pd

def parse_portfolio(file):
    """
    Parses an uploaded Excel/CSV file to extract Tickers and Weights.
    Returns: DataFrame with columns ['Ticker', 'Weight']
    """
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
    except Exception as e:
        return None, f"File format error: {str(e)}"

    # Normalize headers
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Fuzzy Match Logic
    ticker_col = next((c for c in df.columns if any(k in c for k in ['ticker', 'symbol', 'stock', 'asset'])), None)
    weight_col = next((c for c in df.columns if any(k in c for k in ['weight', 'percent', '%', 'value', 'amount'])), None)

    if not ticker_col or not weight_col:
        return None, "Could not find 'Ticker' or 'Weight' columns. Please check your file headers."

    # Data Cleaning
    clean_df = pd.DataFrame()
    clean_df['Ticker'] = df[ticker_col].astype(str).str.upper().str.strip()
    
    # Weight Handling (e.g. 20 vs 0.20)
    raw_weights = pd.to_numeric(df[weight_col], errors='coerce').fillna(0)
    if raw_weights.sum() > 1.5: 
        raw_weights /= 100.0
        
    clean_df['Weight'] = raw_weights / raw_weights.sum() # Normalize to 1.0
    clean_df = clean_df[clean_df['Weight'] > 0] # Remove zero rows
    
    return clean_df, None