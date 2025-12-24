import numpy as np
# Monte Carlo Simulation Function
def run_monte_carlo(expected_returns, cov_matrix, num_portfolios, risk_free_rate):
    num_assets = len(expected_returns)

    results = {
        "returns": [],
        "volatility": [],
        "sharpe": [],
        "weights": []
    }

    for _ in range(num_portfolios):
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)

        portfolio_return = np.dot(weights, expected_returns)
        portfolio_volatility = np.sqrt(
            np.dot(weights.T, np.dot(cov_matrix, weights))
        )

        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility

        results["returns"].append(portfolio_return)
        results["volatility"].append(portfolio_volatility)
        results["sharpe"].append(sharpe_ratio)
        results["weights"].append(weights.tolist())

    return results