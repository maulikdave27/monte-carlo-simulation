#  Portfolio Risk Intelligence v2.4

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![AI-Powered](https://img.shields.io/badge/AI-Gemma%203-blueviolet)](https://ollama.com/library/gemma3)
[![Performance](https://img.shields.io/badge/Engine-Numba%20JIT-orange)](https://numba.pydata.org/)

**Portfolio Risk Intelligence** is a high-performance financial analytics engine designed to bridge the gap between complex mathematical simulations and actionable investment insights. Leveraging **FastAPI**, **Numba-accelerated Monte Carlo simulations**, and **local Gemma 3 AI**, it provides a sub-second, high-fidelity view of portfolio efficiency and risk-adjusted returns.

---

##  Project Novelty & Innovation

What sets **Portfolio Risk Intelligence** apart from conventional financial tools is its unique blend of extreme performance and high-context AI integration:

1.  **Hybrid AI Strategy**: Unlike standard wrappers, this project utilizes a **dual-brain architecture**. It offloads sensitive, real-time sector analysis to a **local Gemma 3 model** via Ollama for privacy and speed, while using **Gemini 2.5 Flash** for high-level institutional reporting.
2.  **JIT-Accelerated Financial Kernels**: Traditionally, Python is considered "slow" for heavy simulations. We overcome this by using **Numba JIT compilation**, translating Python math into machine-level instructions. This allows us to process **4 million iterations** in seconds—performance typically reserved for C++ or Fortran applications.
3.  **Data-Enriched Intelligence**: Most AI financial advisors provide "hallucinated" or generic advice. Our engine injects **vectorized simulation results** and **sector-specific risk contributions** directly into the AI's context, forcing the LLM to provide quantitatively grounded, high-conviction advice.
4.  **Beyond MPT**: While standard tools focus purely on Sharpe Ratios, we integrate **Conditional Value at Risk (CVaR)** and **30-day Rolling Volatility windows** to capture "fat-tail" risks and market regime shifts that traditional Modern Portfolio Theory often ignores.

---

##  Key Features

###  Ultra-Performance Engine
- **Numba JIT Acceleration**: Core mathematical kernels are compiled to machine code for extreme speed.
- **Massive Scale**: Run up to **4,000,000 Monte Carlo iterations** in under 3 seconds.
- **Vectorized Math**: Optimized NumPy-based computation for covariance, volatility, and Sharpe ratio analysis.

#### Performance Benchmarking (2,000,000 Simulations / 7 Assets)
| Implementation Methodology           | Execution Time | Speed Enhancements | Memory Profile |
|--------------------------------------|----------------|--------------------|----------------|
| **Pure Python** (Legacy Loops)       | ~55.20s        | Baseline           | Low, but CPU-bound |
| **Vanilla NumPy** (Vectorized)       | ~3.95s         | ~14x Faster        | Extremely High (OOM risk) |
| **Numba JIT** (Sequential)           | ~5.50s         | ~10x Faster        | Minimal (C-level structs) |
| **Numba JIT** (Parallel + FastMath)  | **~1.78s**     | **~31x Faster**    | Minimal + Scales across Cores |

###  Modern Web Architecture
- **FastAPI Core**: A high-performance REST API handling financial modeling and simulation.
- **Premium UI/UX**: Dark-themed, professional interface with glassmorphism effects and responsive design.
- **Real-Time Visuals**: Interactive Chart.js and Plotly.js visualizations for efficient frontiers, rolling volatility, and sector risk contributions.

###  Dual-AI Intelligence
- **Global Strategist (Gemini 1.5 Flash)**: Generates comprehensive portfolio audit reports and long-term investment summaries.
- **Local Specialist (Gemma 3)**: Provides real-time, privacy-focused **Sector Rotation Analysis** based on live simulation data.
- **Data-Driven Insights**: AI insights are enriched with actual portfolio metrics, sector risk contributions, and ticker-level data.

###  Advanced Risk Analytics
- **2026 Market Calibration**: Integrated forward-looking model using 4.2% Risk-Free Rates and 9.7% Market Return expectations anchored to Jan 2026 benchmarks.
- **Shrinkage Estimators**: Implementation of Numba-accelerated Shrinkage Intensity to reduce estimation error by pulling historical means toward market-wide expectations.
- **Risk-Specific Haircuts**: Multi-tier haircut matrix (ranging from 3 to 15 bps) adjusted for time horizons and investor risk mandates.
- **Sector Rotation**: High-conviction advice on rebalancing across 11+ industry sectors.
- **Risk Decomposition**: Visualize which sectors contribute most to your portfolio's total volatility (Marginal Risk Contribution).
- **Rolling Volatility**: 30-day rolling window comparison specifically calibrated for 2026 market regime shifts.
- **Stress Modeling**: "Black Swan" stress testing (Conditional Value at Risk - CVaR) and historical drawdown analysis.

---

##  Tech Stack

- **Backend**: FastAPI, Uvicorn, Python 3.10+
- **Frontend**: Vanilla HTML5, CSS3 (Tailwind CSS utilities), ES6+ JavaScript
- **Performance**: Numba (Just-In-Time Compilation), NumPy Vectorization, Pandas
- **AI Engines**: 
  - **Local**: Ollama (Gemma 3 4B) for Rotational Analysis
  - **Cloud**: Google Gemini 1.5 Flash for Full Reports
- **Visualization**: Chart.js 4.x, Plotly.js
- **PDF Generation**: ReportLab (for automated strategy PDF downloads)

---

##  Project Setup

Follow these steps to set up the Portfolio Risk Intelligence engine on your local machine.

### 1. Prerequisites
- **Python 3.10+**: Ensure Python is installed (`python --version`).
- **Ollama**: Required for local AI rotational analysis. [Download here](https://ollama.com/).
- **Google Gemini API Key**: Required for full institutional report generation. [Get a key](https://aistudio.google.com/app/apikey).

### 2. Repository Installation
```bash
# Clone the project
git clone <https://github.com/maulikdave27/monte-carlo-simulation>
cd "monte-carlo-simulation-main"

# Install high-performance dependencies
pip install -r requirements.txt
```

### 3. Local AI Preparation (Gemma 3)
The engine uses **Gemma 3 4B** for localized, low-latency sector rotation insights. Ensure Ollama is running in the background, then pull the model:
```bash
ollama pull gemma3:4b
```

### 4. Environment Configuration
Create a `.env` file inside the `misc/` directory to store your API credentials securely:
```bash
mkdir -p misc
echo "GEMINI_API_KEY=your_actual_api_key_here" > misc/.env
```

### 5. Running the Application
Launch the FastAPI server using the provided entry point:
```bash
python main.py
```
After the server starts, navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 📂 Project Architecture

```text
├── main.py               # FastAPI server & API Endpoints
├── frontend/             # Premium UI Assets (HTML, CSS, JS)
├── core/                 # Modular Business Logic
│   ├── engine/           # JIT-Compiled Monte Carlo Simulations
│   ├── comparator/       # Portfolio Audit & Optimization Logic
│   ├── parser/           # Financial Data Ingestion (CSV/Excel)
│   ├── gen_ai/           # AI Insight Engines (Gemini & Gemma)
│   ├── data/             # Historical Universe & Sector Mappings
│   ├── graph/            # Server-side Chart Definitions
│   └── report/           # PDF Generation Engine
├── assets/               # Static Branding & Media
├── test_scenarios/       # Example Portfolios for Testing
└── requirements.txt      # Optimized Project Dependencies
```

---


*Disclaimer: This tool is for educational purposes only. Financial calculations are projections based on historical data and do not constitute financial advice.*
