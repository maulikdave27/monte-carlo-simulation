import pandas as pd

# 1. Standard Format: Testing basic decimal weights
test_standard = pd.DataFrame({
    'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
    'Weight': [0.2, 0.2, 0.2, 0.2, 0.2]
})

# 2. Messy Headers & Percentages: Testing fuzzy matching and division by 100
test_messy = pd.DataFrame({
    'Symbol': ['NVDA', 'TSLA', 'JPM', 'XOM', 'CVX', 'ORCL'],
    'Allocation (%)': [25, 15, 20, 10, 10, 20]
})

# 3. Currency/Value Format: Testing weight calculation from absolute amounts
test_value = pd.DataFrame({
    'Stock': ['AAPL', 'MSFT', 'SPY', 'QQQ', 'GS', 'BAC'],
    'Amount ($)': [5000, 3000, 10000, 2000, 4000, 1000]
})

# 4. Boundary Stress Test: Maximum supported tickers
stress_max_limit = pd.DataFrame({
    'Ticker': ['AAPL', 'AMZN', 'BAC', 'CVX', 'GOOGL', 'GS', 'JPM', 'META', 'MSFT', 'NVDA', 'ORCL', 'QQQ', 'SPY', 'TSLA', 'XOM'],
    'Weight': [1/15]*15
})

# 5. Dirty Data: Testing invalid tickers and normalization
stress_invalid_data = pd.DataFrame({
    'Instrument': ['AAPL', 'NVDA', 'RELIANCE', 'BTC-USD', 'ZOMATO', 'MSFT'],
    'Proportion': [0.4, 0.4, 0.2, 1.5, 0.0, 0.2]
})

# Save all files to your current directory
test_standard.to_csv('test/test_standard.csv', index=False)
test_messy.to_csv('test/test_messy.csv', index=False)
test_value.to_csv('test/test_value.csv', index=False)
stress_max_limit.to_csv('test/stress_max_limit.csv', index=False)
stress_invalid_data.to_csv('test/stress_invalid_data.csv', index=False)

print("✅ All 5 test and stress files have been created in your folder.")