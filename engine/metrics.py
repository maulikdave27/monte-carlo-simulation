import numpy as np

TRADING_DAYS = 252

def compute_annual_metrics(daily_returns):
    mean_daily = daily_returns.mean()
    cov_daily = daily_returns.cov()

    annual_returns = mean_daily * TRADING_DAYS
    annual_cov = cov_daily * TRADING_DAYS

    return annual_returns.values, annual_cov.values