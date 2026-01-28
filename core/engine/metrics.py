import numpy as np
from numba import njit

TRADING_DAYS = 252

# === 2026 Market Calibration ===
RISK_FREE_RATE = 0.042  # 4.2% (10Y Treasury Jan 2026)
MARKET_RETURN = 0.097   # 9.7% (Expected equity market return)

# Shrinkage intensity by time horizon [1-3, 3-6, 6+]
SHRINKAGE_ARR = np.array([0.60, 0.40, 0.25])

# Risk-specific haircuts: Row=Horizon (1-3, 3-6, 6+), Col=Preference (Low, Med, High)
HAIRCUTS_ARR = np.array([
    [0.015, 0.010, 0.005],  # 1-3 years
    [0.012, 0.008, 0.004],  # 3-6 years
    [0.010, 0.006, 0.003]   # 6+ years
])

# Return caps by horizon
MAX_RETURNS_ARR = np.array([0.14, 0.16, 0.18])

# Transaction Costs
TOTAL_FRICTION = 0.0015 # 15 bps total

@njit(fastmath=True)
def _numba_metrics_kernel(mean_daily, raw_cov, raw_semi_cov, horizon_idx, risk_idx):
    """Jit-compiled kernel for metrics estimation"""
    
    # Step 1: Annualize raw historical returns
    raw_annual = mean_daily * TRADING_DAYS
    
    # Step 2: Apply shrinkage toward market
    lambda_h = SHRINKAGE_ARR[horizon_idx]
    shrunk = lambda_h * MARKET_RETURN + (1 - lambda_h) * raw_annual
    
    # Step 3: Apply risk-specific haircut
    haircut = HAIRCUTS_ARR[horizon_idx, risk_idx]
    adjusted = shrunk - haircut
    
    # Step 4: Apply return cap
    max_ret = MAX_RETURNS_ARR[horizon_idx]
    capped = np.empty_like(adjusted)
    for i in range(len(adjusted)):
        capped[i] = min(adjusted[i], max_ret)
    
    # Step 5: Apply Salami Slicing & Floor
    frictional_adjusted = capped - TOTAL_FRICTION
    
    annual_returns = np.empty_like(frictional_adjusted)
    for i in range(len(frictional_adjusted)):
        annual_returns[i] = max(frictional_adjusted[i], RISK_FREE_RATE)
    
    # Step 6: Annualize Covariance
    annual_cov = raw_cov * TRADING_DAYS
    annual_semi_cov = raw_semi_cov * TRADING_DAYS
    
    return annual_returns, annual_cov, annual_semi_cov

def compute_annual_metrics(daily_returns, target_return=0, 
                          time_horizon="3-6 years", risk_preference="Medium"):
    """
    Interface for annualized metrics with Numba acceleration.
    """
    # 1. Map string parameters to indices for Numba
    horizons = ["1-3 years", "3-6 years", "6+ years"]
    # Handle dash variances
    clean_horizon = time_horizon.replace("–", "-")
    try:
        hor_idx = horizons.index(clean_horizon)
    except ValueError:
        hor_idx = 1 # Default to 3-6 years
        
    preferences = ["Low", "Medium", "High"]
    try:
        risk_idx = preferences.index(risk_preference)
    except ValueError:
        risk_idx = 1 # Default to Medium

    # 2. Base Calculations (Pandas/NumPy)
    mean_daily = daily_returns.mean().values
    cov_daily = daily_returns.cov().values
    
    # Calculate Downside Semi-Covariance Matrix
    dr = daily_returns.values
    downside_dr = np.where(dr > target_return, target_return, dr)
    # NumPy cov is slower than pandas but needed for JIT consistency? 
    # Actually we can do it here and pass values.
    semi_cov_daily = np.cov(downside_dr, rowvar=False)

    # 3. Call JIT Kernel
    return _numba_metrics_kernel(
        mean_daily, 
        cov_daily, 
        semi_cov_daily, 
        hor_idx, 
        risk_idx
    )