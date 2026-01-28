import numpy as np

def find_max_sharpe(results):
    sharpe_ratios = np.array(results["sharpe"])
    idx = sharpe_ratios.argmax()

    return {
        "expected_return": results["returns"][idx],
        "volatility": results["volatility"][idx],
        "sharpe_ratio": results["sharpe"][idx],
        "weights": results["weights"][idx]
    }