# Asset Sector Mapping
# Maps each supported ticker to its Primary Sector

ASSET_SECTOR_MAP = {
    # Technology
    "AAPL": "Technology",
    "NVDA": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Technology",
    "AMZN": "Technology",
    "META": "Technology",
    "TSLA": "Technology",
    "ORCL": "Technology",

    # Financials
    "JPM": "Financials",
    "BAC": "Financials",
    "WFC": "Financials",
    "GS": "Financials",
    "V": "Financials",

    # Energy
    "XOM": "Energy",
    "CVX": "Energy",
    "SLB": "Energy",
    "COP": "Energy",
    "EOG": "Energy",

    # Consumer Staples
    "PG": "Consumer Staples",
    "KO": "Consumer Staples",
    "PEP": "Consumer Staples",
    "WMT": "Consumer Staples",
    "COST": "Consumer Staples",

    # Healthcare
    "JNJ": "Healthcare",
    "PFE": "Healthcare",
    "UNH": "Healthcare"
}

def get_sector_weights(tickers, weights):
    """
    Aggregates portfolio weights by sector.
    
    Args:
        tickers (list): List of ticker symbols
        weights (list): List of corresponding weights
        
    Returns:
        dict: {Sector: Weight} sorted by weight descending
        dict: {Ticker: Sector} map (for reference)
    """
    sector_weights = {}
    
    for t, w in zip(tickers, weights):
        # Default to 'Other' if not in map
        sector = ASSET_SECTOR_MAP.get(t, "Other")
        sector_weights[sector] = sector_weights.get(sector, 0.0) + w
        
    # Sort by weight descending
    sorted_weights = dict(sorted(sector_weights.items(), key=lambda item: item[1], reverse=True))
    
    return sorted_weights
