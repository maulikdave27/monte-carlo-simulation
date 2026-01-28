import numpy as np
from numba import njit, prange

@njit(parallel=True, fastmath=True)
def _numba_mc_kernel(exp_ret, cov, semi_cov, num_portfolios, rf_rate, seed):
    """Integrated JIT kernel for weight generation and metrics"""
    np.random.seed(seed)
    num_assets = exp_ret.shape[0]
    
    returns = np.zeros(num_portfolios)
    volatility = np.zeros(num_portfolios)
    downside_vol = np.zeros(num_portfolios)
    cvar = np.zeros(num_portfolios)
    sharpe = np.zeros(num_portfolios)
    sortino = np.zeros(num_portfolios)
    all_weights = np.zeros((num_portfolios, num_assets))
    
    for i in prange(num_portfolios):
        # 1. Generate Weights
        w = np.random.random(num_assets)
        w_sum = 0.0
        for j in range(num_assets):
            w_sum += w[j]
        
        for j in range(num_assets):
            w[j] = w[j] / w_sum
            all_weights[i, j] = w[j]
        
        # 2. Performance Metrics
        ret = 0.0
        for j in range(num_assets):
            ret += w[j] * exp_ret[j]
        returns[i] = ret
        
        var = 0.0
        d_var = 0.0
        for row in range(num_assets):
            tmp = 0.0
            d_tmp = 0.0
            for col in range(num_assets):
                tmp += w[col] * cov[row, col]
                d_tmp += w[col] * semi_cov[row, col]
            var += w[row] * tmp
            d_var += w[row] * d_tmp
            
        vol = np.sqrt(var)
        d_vol = np.sqrt(d_var)
        
        volatility[i] = vol
        downside_vol[i] = d_vol
        cvar[i] = -ret + (2.063 * vol)
        
        if vol > 0:
            sharpe[i] = (ret - rf_rate) / vol
        if d_vol > 0:
            sortino[i] = (ret - rf_rate) / d_vol
            
    return returns, volatility, sharpe, sortino, cvar, all_weights

# Monte Carlo Simulation Function
def run_monte_carlo(expected_returns, cov_matrix, semi_cov_matrix, num_portfolios, risk_free_rate):
    # Call Fully Integrated JIT Kernel
    seed = np.random.randint(1, 100000)
    
    port_returns, port_vol, sharpe_ratios, sortino_ratios, cvar_95, weights = _numba_mc_kernel(
        expected_returns, 
        cov_matrix, 
        semi_cov_matrix, 
        num_portfolios,
        risk_free_rate,
        seed
    )

    return {
        "returns": port_returns,
        "volatility": port_vol,
        "sharpe": sharpe_ratios,
        "sortino": sortino_ratios,
        "cvar": cvar_95,
        "weights": weights
    }