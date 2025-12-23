import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

from engine.data_loader import load_returns
from engine.metrics import compute_annual_metrics
from engine.monte_carlo import run_monte_carlo

# ----------------------------
# CONFIGURATION
# ----------------------------
RETURNS_PATH = "data/daily_returns.csv"
NUM_PORTFOLIOS = 90000

RISK_FREE_MAP = {
    "1–3 years": 0.015,
    "3–6 years": 0.02,
    "6+ years": 0.025
}

VOL_PENALTY = {
    "Low": 1.5,
    "Medium": 1.0,
    "High": 0.7
}

HORIZON_YEARS = {
    "1–3 years": 1,
    "3–6 years": 3,
    "6+ years": 5
}

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def compute_asset_risk_return(returns_df, horizon):
    years = HORIZON_YEARS[horizon]
    asset_returns = returns_df.mean() * 252 * years
    asset_volatility = returns_df.std() * np.sqrt(252 * years)

    return pd.DataFrame({
        "Return": asset_returns,
        "Volatility": asset_volatility
    })


# ----------------------------
# STREAMLIT UI
# ----------------------------
st.set_page_config(
    page_title="Portfolio Risk Optimization",
    layout="centered"
)

st.title("📊 Portfolio Risk Optimization Engine")
st.markdown(
    "Monte Carlo–based portfolio optimization with user-defined risk appetite "
    "and investment horizon."
)

# ----------------------------
# LOAD DATA
# ----------------------------
returns_df = load_returns(RETURNS_PATH)
available_assets = list(returns_df.columns)

# ----------------------------
# USER INPUTS
# ----------------------------
st.header("🔧 Configure Your Portfolio")

selected_assets = st.multiselect(
    "Select Stocks (5–15)",
    options=available_assets,
    default=available_assets[:6]
)

forecast_horizon = st.selectbox(
    "Investment Horizon",
    options=list(RISK_FREE_MAP.keys())
)

risk_pref = st.selectbox(
    "Risk Preference",
    options=list(VOL_PENALTY.keys())
)

run_button = st.button("Run Optimization")

# ----------------------------
# EXECUTION
# ----------------------------
if run_button:
    if not (5 <= len(selected_assets) <= 15):
        st.error("Please select between 5 and 15 stocks.")
        st.stop()

    st.subheader("⚙️ Running Simulation...")

    filtered_returns = returns_df[selected_assets]

    exp_returns, cov_matrix = compute_annual_metrics(filtered_returns)

    results = run_monte_carlo(
        expected_returns=exp_returns,
        cov_matrix=cov_matrix,
        num_portfolios=NUM_PORTFOLIOS,
        risk_free_rate=RISK_FREE_MAP[forecast_horizon]
    )

    returns_arr = np.array(results["returns"])
    vols_arr = np.array(results["volatility"])

    score = returns_arr / (vols_arr * VOL_PENALTY[risk_pref])
    idx = score.argmax()

    optimal = {
        "expected_return": returns_arr[idx],
        "volatility": vols_arr[idx],
        "weights": results["weights"][idx]
    }

    # ----------------------------
    # RESULTS
    # ----------------------------
    st.success("Optimization Completed")

    col1, col2 = st.columns(2)
    col1.metric("Expected Annual Return", f"{optimal['expected_return']:.2%}")
    col2.metric("Annual Volatility", f"{optimal['volatility']:.2%}")

    # ----------------------------
    # ALLOCATION TABLE
    # ----------------------------
    st.subheader("📌 Optimal Asset Allocation")

    allocation_df = pd.DataFrame({
        "Asset": selected_assets,
        "Weight (%)": np.array(optimal["weights"]) * 100
    })

    st.dataframe(
        allocation_df.style.format({"Weight (%)": "{:.2f}"})
    )

    # ----------------------------
    # PIE CHART
    # ----------------------------
    st.subheader("🥧 Portfolio Weight Distribution")

    fig1, ax1 = plt.subplots(figsize=(6, 6))
    ax1.pie(
        optimal["weights"],
        labels=selected_assets,
        autopct="%1.1f%%",
        startangle=90
    )
    ax1.axis("equal")

    st.pyplot(fig1)

    # ----------------------------
    # RISK vs RETURN SCATTER
    # ----------------------------
    st.subheader("📈 Risk vs Return of Selected Assets")

    asset_metrics = compute_asset_risk_return(
        filtered_returns,
        forecast_horizon
    )

    fig2, ax2 = plt.subplots(figsize=(8, 6))

    sns.scatterplot(
        x=asset_metrics["Volatility"],
        y=asset_metrics["Return"],
        s=120,
        ax=ax2
    )

    for asset in asset_metrics.index:
        ax2.text(
            asset_metrics.loc[asset, "Volatility"] * 1.01,
            asset_metrics.loc[asset, "Return"] * 1.01,
            asset,
            fontsize=9
        )

    ax2.set_xlabel("Annualized Volatility")
    ax2.set_ylabel("Annualized Return")
    ax2.set_title(f"Risk–Return Profile ({forecast_horizon})")

    st.pyplot(fig2)

    # ----------------------------
    # PORTFOLIO EFFICIENCY FRONTIER
    # ----------------------------
    st.subheader("Monte Carlo Efficient Frontier")

    fig3, ax3 = plt.subplots(figsize=(8, 6))

    sc = ax3.scatter(
        vols_arr,
        returns_arr,
        c=returns_arr / vols_arr,
        cmap="viridis",
        alpha=0.35
    )

    ax3.scatter(
        optimal["volatility"],
        optimal["expected_return"],
        color="red",
        s=160,
        marker="*",
        label="Optimal Portfolio"
    )

    ax3.set_xlabel("Annualized Volatility")
    ax3.set_ylabel("Expected Return")
    ax3.set_title("Efficient Frontier (Monte Carlo Simulation)")
    ax3.legend()

    plt.colorbar(sc, label="Sharpe Ratio")

    st.pyplot(fig3)

    st.caption(
        f"Risk Preference: {risk_pref} | Horizon: {forecast_horizon} | "
        f"Simulated Portfolios: {NUM_PORTFOLIOS}"
    )