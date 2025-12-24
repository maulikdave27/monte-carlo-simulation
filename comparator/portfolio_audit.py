import numpy as np
import pandas as pd
from engine import metrics, monte_carlo

def run_audit(user_df, historical_data, risk_preference="High", risk_free_rate=0.02, num_simulations=400000):
    """
    Compares User vs. Optimal Portfolio.
    """
    # 1. Filter for valid tickers
    user_tickers = user_df['Ticker'].tolist()
    valid_tickers = [t for t in user_tickers if t in historical_data.columns]
    
    if len(valid_tickers) < 2:
        return None, "Not enough valid tickers found in history database. Need at least 2 matching stocks."

    # 2. Prepare Data
    subset_data = historical_data[valid_tickers]
    mean_ret, cov_mat = metrics.compute_annual_metrics(subset_data)
    
    # 3. User Metrics Calculation
    # Align user weights to the valid subset
    valid_user_df = user_df[user_df['Ticker'].isin(valid_tickers)].copy()
    valid_user_df['Weight'] = valid_user_df['Weight'] / valid_user_df['Weight'].sum()
    
    # Create aligned weight array
    user_weights = valid_user_df.set_index('Ticker')['Weight'].reindex(valid_tickers).fillna(0).values
    
    user_ret = np.dot(user_weights, mean_ret)
    user_vol = np.sqrt(np.dot(user_weights.T, np.dot(cov_mat, user_weights)))
    user_sharpe = (user_ret - risk_free_rate) / user_vol

    # 4. Run Monte Carlo Simulation
    sim_results = monte_carlo.run_monte_carlo(mean_ret, cov_mat, num_simulations, risk_free_rate)
    
    # 5. Find Optimal Portfolio
    # High Risk = Max Sharpe (Aggressive)
    # Low Risk = Min Volatility (Conservative)
    if risk_preference == "High":
        best_idx = np.argmax(sim_results['sharpe'])
    elif risk_preference == "Low":
        best_idx = np.argmin(sim_results['volatility'])
    else: 
        # Medium: Find max sharpe but penalize extreme volatility (Simplified logic)
        # Or just default to Max Sharpe for now as per "Optimal" definition
        best_idx = np.argmax(sim_results['sharpe'])

    opt_stats = {
        "return": sim_results['returns'][best_idx],
        "volatility": sim_results['volatility'][best_idx],
        "sharpe": sim_results['sharpe'][best_idx],
        "weights": sim_results['weights'][best_idx]
    }

    return {
        "user": {"return": user_ret, "volatility": user_vol, "sharpe": user_sharpe, "weights": user_weights},
        "optimal": opt_stats,
        "tickers": valid_tickers,
        "num_simulations": len(sim_results['returns']),
        "simulation_data": sim_results # Needed for graphs
    }, None