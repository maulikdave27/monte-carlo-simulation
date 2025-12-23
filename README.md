#  Portfolio Risk Optimization Engine

A professional-grade, Monte Carlo–based portfolio optimization application built with **Streamlit**. This tool allows users to find the optimal asset allocation based on their risk appetite and investment horizon using historical data.

##  Features

-   **Monte Carlo Simulation:** Generates 30,000 random portfolios to find the efficient frontier.
-   **Risk Personalization:** Adjust optimization based on "Low", "Medium", or "High" risk preferences.
-   **Investment Horizon Support:** Tailored risk-free rates and return projections for different timeframes (1–3, 3–6, and 6+ years).
-   **Interactive Visualizations:**
    -   Optimal Asset Weight Distribution (Pie Chart).
    -   Risk vs. Return Scatter Plots for individual assets.
    -   Efficient Frontier visualization with the Maxwell-Sharpe optimal portfolio identified.
-   **Flexible Asset Selection:** Choose between 5 to 15 assets for your custom portfolio.

##  Tech Stack

-   **Frontend:** [Streamlit](https://streamlit.io/)
-   **Data Processing:** [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
-   **Visualization:** [Matplotlib](https://matplotlib.org/), [Seaborn](https://seaborn.pydata.org/)

##  Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Code
```

### 2. Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
streamlit run streamlit_app.py
```

##  Project Structure

-   `streamlit_app.py`: Main Streamlit application entry point.
-   `engine/`: Core logic modules.
    -   `data_loader.py`: Handles CSV data ingestion.
    -   `metrics.py`: Computes annualized returns and covariance matrices.
    -   `monte_carlo.py`: Runs the stochastic simulation.
    -   `optimizer.py`: Identifies the optimal portfolio from simulation results.
-   `data/`: Contains historical returns data (e.g., `daily_returns.csv`).

##  Requirements

The application requires Python 3.8+ and the libraries listed in `requirements.txt`.

---
