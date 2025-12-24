# Portfolio Risk Optimization Engine 

A professional-grade, Monte Carlo–based portfolio optimization application built with **Streamlit**. This tool allows users to analyze their current portfolio and find the optimal asset allocation based on their risk appetite and investment horizon using historical data.

##  Features

-   **Dynamic Monte Carlo Simulation:** Run up to 1,000,000 simulations to map the Efficient Frontier. Controls provided via sidebar slider.
-   **Portfolio Auditing:** Upload your existing portfolio (CSV/Excel) and compare its performance metrics against AI-optimized strategies.
-   **Risk Personalization:** Adjust optimization strategy based on "Low", "Medium", or "High" risk preferences.
-   **Investment Horizon Support:** Tailored risk-free rates and return projections for different timeframes (1–3, 3–6, and 6+ years).
-   **Interactive Visualizations (Plotly):**
    -   **Efficiency Frontier:** Visualize the risk vs. return cloud with your current portfolio vs. the optimal point.
    -   **Allocation Comparison:** Side-by-side Asset Weight Distribution (Donut Charts).
-   **Flexible Input:** Support for file uploads or manual asset selection for testing.

##  Tech Stack

-   **Frontend:** [Streamlit](https://streamlit.io/)
-   **Data Processing:** [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
-   **Visualization:** [Plotly](https://plotly.com/python/)
-   **Backend Logic:** Custom modular engine for financial metrics and stochastic simulations.

##  Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/maulikdave27/monte-carlo-simulation.git
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

## 📂 Project Structure

-   `streamlit_app.py`: Main Streamlit application entry point.
-   `engine/`: Core mathematical logic.
    -   `metrics.py`: Computes annualized returns and covariance matrices.
    -   `monte_carlo.py`: Runs the stochastic simulations.
    -   `optimizer.py`: Logic for finding Max Sharpe or Min Volatility points.
-   `comparator/`: Handles the logic for auditing user-uploaded portfolios.
-   `parser/`: Logic for parsing Excel and CSV portfolio files.
-   `data/`: Contains historical returns data (`daily_returns.csv`).

## 📋 Requirements

The application requires Python 3.8+ and the libraries listed in `requirements.txt`.

---
Developed as part of the Major Project 2025.
