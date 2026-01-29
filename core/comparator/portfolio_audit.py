import numpy as np
import pandas as pd
from core.engine import metrics, monte_carlo

def run_audit(user_df, historical_data, risk_preference="High", risk_free_rate=0.02, num_simulations=400000, time_horizon="3-6 years"):
    """
    Compares User vs. Optimal Portfolio with time-horizon aware estimates.
    
    Args:
        time_horizon: "1-3 years", "3-6 years", or "6+ years"
    """
    # 1. Filter for valid tickers
    user_tickers = user_df['Ticker'].tolist()
    valid_tickers = [t for t in user_tickers if t in historical_data.columns]
    
    if len(valid_tickers) < 7:
        return None, "Not enough valid tickers found in history database. Need at least 7 matching stocks (26 supported)."

    # 2. Prepare Data
    subset_data = historical_data[valid_tickers]
    mean_ret, cov_mat, semi_cov_mat = metrics.compute_annual_metrics(
        subset_data, 
        target_return=0,
        time_horizon=time_horizon,
        risk_preference=risk_preference
    )
    
    # 3. User Metrics Calculation
    # Align user weights to the valid subset
    valid_user_df = user_df[user_df['Ticker'].isin(valid_tickers)].copy()
    valid_user_df['Weight'] = valid_user_df['Weight'] / valid_user_df['Weight'].sum()
    
    # Create aligned weight array
    user_weights = valid_user_df.set_index('Ticker')['Weight'].reindex(valid_tickers).fillna(0).values
    
    user_ret = np.dot(user_weights, mean_ret)
    user_vol = np.sqrt(np.dot(user_weights.T, np.dot(cov_mat, user_weights)))
    user_downside_vol = np.sqrt(np.dot(user_weights.T, np.dot(semi_cov_mat, user_weights)))
    
    user_sharpe = (user_ret - risk_free_rate) / user_vol
    user_sortino = (user_ret - risk_free_rate) / user_downside_vol if user_downside_vol != 0 else 0

    # 4. Run Monte Carlo Simulation
    results = monte_carlo.run_monte_carlo(mean_ret, cov_mat, semi_cov_mat, num_simulations, risk_free_rate)
    
    # CVaR 95% (Parametric Expected Shortfall)
    cvar_95 = results.get('cvar', [])

    # Diversification Check (HHI)
    # HHI = Sum of squared weights. Lower is better.
    # 1.0 = Monopoly (100% in one asset), 1/N = Perfect diversification
    hhi_scores = np.sum(np.array(results['weights']) ** 2, axis=1)

    best_idx = -1
    
    # CONSTRAINT LOOPS (Fallback Logic)
    # We try strict constraints first. If no portfolio found, we loosen them.
    # Constraints: Max Single Asset Weight (Fiduciary Standard: 20%)
    constraints = [0.20, 0.40, 0.60, 1.0] # start with strict 20%, then loosen

    for max_weight in constraints:
        # Filter indices that satisfy the max weight constraint
        valid_indices = np.where(np.max(np.array(results['weights']), axis=1) <= max_weight)[0]
        
        if len(valid_indices) == 0:
            continue # Try next restraint

        # Subset results to valid portfolios
        valid_sharpe = np.array(results['sharpe'])[valid_indices]
        valid_vol = np.array(results['volatility'])[valid_indices]
        valid_ret = np.array(results['returns'])[valid_indices]

        if risk_preference == "High":
            # Aggressive: Max Sortino (Best Risk-Adjusted Return for Downside)
            # This ensures we get high returns but penalize "bad" volatility.
            local_best = np.argmax(np.array(results['sortino'])[valid_indices])
            best_idx = valid_indices[local_best]
            
        elif risk_preference == "Low":
            # Conservative: Min Volatility
            local_best = np.argmin(valid_vol)
            best_idx = valid_indices[local_best]
            
        else: 
            # Medium: Max Sharpe (Tangent)
            local_best = np.argmax(valid_sharpe)
            best_idx = valid_indices[local_best]
            
        # If we found a valid index, break the loop
        if best_idx != -1:
            break
            
    # CRITICAL FALLBACK: If 2M simulations failed all constraints (unlikely), just take raw best
    if best_idx == -1:
        best_idx = np.argmax(results['sharpe'])

    # Get stats for the chosen portfolio
    chosen_hhi = hhi_scores[best_idx]
    div_score = 1 - chosen_hhi # Higher is better (0 to 1 scale roughly)

    opt_stats = {
        "return": results['returns'][best_idx],
        "volatility": results['volatility'][best_idx],
        "sharpe": results['sharpe'][best_idx],
        "sortino": results['sortino'][best_idx],
        "cvar": cvar_95[best_idx] if len(cvar_95) > 0 else 0, # Handle if CVaR not computed yet
        "weights": results['weights'][best_idx],
        "hhi": chosen_hhi,
        "diversification_score": div_score
    }
    
    # 5. Stress Testing (Black Swan Scenario: Correlation -> 1.0)
    # Rule: Drawdown check for Low Risk (>15% rejection scenario)
    # For a high-level estimate: Stress Drawdown = ES (CVaR) scale factor
    # In a systemic collapse (Correlation=1), portfolio vol approach sum of asset vols.
    # We'll use a 2008-Scenario ES estimate.
    stress_drawdown = opt_stats['cvar'] * 1.5 # 1.5x escalation factor for systemic crash
    opt_stats['stress_drawdown'] = stress_drawdown
    
    # Calculate User CVaR for comparison
    user_cvar = -user_ret + (2.063 * user_vol)
    user_hhi = np.sum(user_weights ** 2)
    user_stress_drawdown = user_cvar * 1.5

    return {
        "user": {
            "return": user_ret, "volatility": user_vol, "sharpe": user_sharpe, 
            "sortino": user_sortino, "cvar": user_cvar, "weights": user_weights,
            "hhi": user_hhi, "diversification_score": 1 - user_hhi,
            "stress_drawdown": user_stress_drawdown
        },
        "optimal": opt_stats,
        "tickers": valid_tickers,
        "num_simulations": len(results['returns']),
        "simulation_data": results,
        "cov_matrix": cov_mat  # Add covariance matrix for volatility contribution
    }, None