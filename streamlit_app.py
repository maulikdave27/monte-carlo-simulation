import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os
import inspect

# --- IMPORT MODULES ---
# Assumes you have created the 'parser' and 'comparator' folders as discussed
try:
    from parser import excel_parser
    from comparator import portfolio_audit
except ImportError:
    st.error("⚠️ Modules not found. Please ensure 'parser/' and 'comparator/' folders exist in the same directory.")
    st.stop()

# --- CONFIGURATION ---
st.set_page_config(page_title="Portfolio Risk Intelligence", layout="wide")

# Path to your historical data
DATA_PATH = "data/daily_returns.csv"

# Configuration Maps
RISK_FREE_MAP = {
    "1–3 years": 0.015,
    "3–6 years": 0.02,
    "6+ years": 0.025
}

# --- PLOTLY VISUALIZATION FUNCTIONS ---
def plot_allocation_comparison(tickers, user_weights, optimal_weights):
    """
    Generates side-by-side Donut charts for User vs Optimal Portfolio.
    """
    fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]],
                        subplot_titles=['Your Portfolio', 'AI Optimized'])

    fig.add_trace(go.Pie(labels=tickers, values=user_weights, name="User", hole=.4), 1, 1)
    fig.add_trace(go.Pie(labels=tickers, values=optimal_weights, name="Optimal", hole=.4), 1, 2)

    fig.update_layout(title_text="Asset Allocation Comparison", showlegend=True)
    return fig

def plot_efficient_frontier(sim_data, user_metrics, opt_metrics):
    """
    Generates the Efficient Frontier scatter plot with User vs Optimal markers.
    """
    # Downsample for speed (plot 2000 points instead of 30k)
    # Ensure we don't try to sample more than we have
    n_points = min(len(sim_data['returns']), 2000)
    idx = np.random.choice(len(sim_data['returns']), n_points, replace=False)
    
    fig = go.Figure()

    # 1. The Cloud (All Possibilities)
    fig.add_trace(go.Scatter(
        x=np.array(sim_data['volatility'])[idx],
        y=np.array(sim_data['returns'])[idx],
        mode='markers',
        marker=dict(color='lightgrey', size=3, opacity=0.5),
        name='Simulations'
    ))

    # 2. User Point (Red)
    fig.add_trace(go.Scatter(
        x=[user_metrics['volatility']],
        y=[user_metrics['return']],
        mode='markers+text',
        marker=dict(color='red', size=15, symbol='x'),
        text=['YOU'], textposition="top center",
        name='Your Portfolio'
    ))

    # 3. Optimal Point (Green)
    fig.add_trace(go.Scatter(
        x=[opt_metrics['volatility']],
        y=[opt_metrics['return']],
        mode='markers+text',
        marker=dict(color='green', size=15, symbol='star'),
        text=['OPTIMAL'], textposition="top center",
        name='AI Optimized'
    ))

    fig.update_layout(
        title="Risk vs. Return (Efficiency Frontier)",
        xaxis_title="Annual Risk (Volatility)",
        yaxis_title="Expected Annual Return",
        showlegend=True
    )
    return fig

# --- MAIN APP LOGIC ---
def main():
    st.title("📊 AI Portfolio Risk Intelligence")
    st.markdown("Upload your portfolio (Excel/CSV) to see how it compares to an AI-Optimized strategy.")

    # Sidebar Inputs
    with st.sidebar:
        st.header("Simulation Settings")
        
        horizon = st.selectbox(
            "Investment Horizon",
            options=list(RISK_FREE_MAP.keys()),
            index=0
        )
        
        risk_pref = st.selectbox(
            "Risk Preference",
            options=["Low", "Medium", "High"],
            index=2
        )
        
        # Dynamically get default from backend
        sig = inspect.signature(portfolio_audit.run_audit)
        backend_default = sig.parameters['num_simulations'].default
        
        num_sims = st.slider(
            "Number of Simulations",
            min_value=10000,
            max_value=1000000,
            value=int(backend_default),
            step=10000,
            help="Higher numbers increase accuracy but take longer to compute."
        )
        
        st.divider()
        
        # Input Method Toggle
        input_method = st.radio("Input Method", ["Upload File", "Manual Selection (Test)"])
        
        user_df = None
        
        if input_method == "Upload File":
            uploaded_file = st.file_uploader("Upload Portfolio", type=['csv', 'xlsx'])
            if uploaded_file:
                st.info("Parsing file...")
                user_df, error = excel_parser.parse_portfolio(uploaded_file)
                if error:
                    st.error(error)
                    user_df = None
                else:
                    st.success(f"Loaded {len(user_df)} tickers.")
                    
        else: # Manual Selection
            # Helper to create a dummy dataframe for testing without a file
            available_assets = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "JPM", "BAC", "WFC", "XOM", "CVX", "SPY", "QQQ", "GLD"] 
            selected = st.multiselect("Select Assets (Assume Equal Weight)", available_assets, default=["AAPL", "JPM", "XOM", "NVDA", "SPY"])
            if selected:
                # Create Equal Weighted DF
                weights = [1.0/len(selected)] * len(selected)
                user_df = pd.DataFrame({'Ticker': selected, 'Weight': weights})

    # Execution Area
    if user_df is not None:
        if st.button("Run Risk Analysis"):
            
            # Load History
            if not os.path.exists(DATA_PATH):
                st.error(f"Data file not found at {DATA_PATH}")
                st.stop()
                
            hist_data = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
            risk_free_rate = RISK_FREE_MAP[horizon]

            with st.spinner(f"Running {num_sims:,} Monte Carlo Simulations..."):
                # CALL THE COMPARATOR
                result, err = portfolio_audit.run_audit(
                    user_df, 
                    hist_data, 
                    risk_preference=risk_pref, 
                    risk_free_rate=risk_free_rate,
                    num_simulations=num_sims
                )

            if err:
                st.error(err)
            else:
                # --- RESULTS DASHBOARD ---
                st.divider()
                
                # 1. High-Level Metrics
                col1, col2, col3 = st.columns(3)
                
                # User Stats
                with col1:
                    st.subheader("Your Portfolio")
                    st.metric("Expected Return", f"{result['user']['return']:.2%}")
                    st.metric("Annual Risk", f"{result['user']['volatility']:.2%}")
                    st.metric("Sharpe Ratio", f"{result['user']['sharpe']:.2f}")

                # Optimal Stats
                with col2:
                    st.subheader(f"AI Optimized ({risk_pref})")
                    st.metric("Expected Return", f"{result['optimal']['return']:.2%}", 
                              delta=f"{(result['optimal']['return'] - result['user']['return']):.2%}")
                    st.metric("Annual Risk", f"{result['optimal']['volatility']:.2%}",
                              delta=f"{(result['optimal']['volatility'] - result['user']['volatility']):.2%}", delta_color="inverse")
                    st.metric("Sharpe Ratio", f"{result['optimal']['sharpe']:.2f}",
                              delta=f"{(result['optimal']['sharpe'] - result['user']['sharpe']):.2f}")

                # Insight Box
                with col3:
                    st.info(f"**Insight:** The AI found a strategy that improves your Sharpe Ratio by **{(result['optimal']['sharpe'] - result['user']['sharpe']):.2f}**. Check the Efficiency Frontier below.")

                st.divider()

                # 2. Visualizations
                tab1, tab2 = st.tabs(["Efficiency Frontier", "Allocation Split"])
                
                with tab1:
                    frontier_fig = plot_efficient_frontier(
                        result['simulation_data'], 
                        result['user'], 
                        result['optimal']
                    )
                    st.plotly_chart(frontier_fig, use_container_width=True)
                
                with tab2:
                    pie_fig = plot_allocation_comparison(
                        result['tickers'], 
                        result['user']['weights'], 
                        result['optimal']['weights']
                    )
                    st.plotly_chart(pie_fig, use_container_width=True)
                
                # --- POSTSCRIPT ---
                st.markdown(f"""
                ---
                *Computed using **{result['num_simulations']:,}** simulations. The efficiency frontier visualization is downsampled to 2,000 points for performance.*
                """)
    
    elif input_method == "Upload File":
        st.info("👋 Please upload a portfolio file to begin.")

if __name__ == "__main__":
    main()