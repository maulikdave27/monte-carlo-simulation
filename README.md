# 🚀 Portfolio Risk Intelligence v5.0 (Ultra Performance)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![AI-Powered](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-blueviolet)](https://aistudio.google.com/)
[![Performance](https://img.shields.io/badge/Engine-Numba%20JIT-orange)](https://numba.pydata.org/)

**Portfolio Risk Intelligence** is a high-performance financial analytics engine designed to bridge the gap between complex mathematical simulations and actionable investment insights. Leveraging **FastAPI**, **Numba-accelerated Monte Carlo simulations**, and **Google's Gemini 1.5 Flash**, it provides a sub-second, high-fidelity view of portfolio efficiency and risk-adjusted returns.

---

## ✨ Key Features

### ⚡ Ultra-Performance Engine
- **Numba JIT Acceleration**: Core mathematical kernels are compiled to machine code for extreme speed.
- **Massive Scale**: Run up to **4,000,000 Monte Carlo iterations** in under 3 seconds.
- **Integrated Weight Kernels**: Optimized random weight generation inside the compiled simulation pipeline.

### 💻 Modern Web Architecture
- **FastAPI Core**: A high-performance REST API handling financial modeling and simulation.
- **Vanilla Frontend**: A professional, responsive interface built for reliability and minimalism.
- **Real-Time Visuals**: Interactive Plotly.js charts for efficient frontier and allocation analysis.

### 🤖 AI-Driven Insights
- **Institutional Specialist**: Integrated with **Google Gemini 1.5 Flash** for qualitative portfolio auditing.
- **Sector Intelligence**: Automatic sector mapping and diversification gap analysis.
- **Stress Modeling**: 2008-scenario "Black Swan" stress testing (Black Swan Drawdown).

---

## 🛠 Tech Stack

- **Backend**: FastAPI, Uvicorn
- **Frontend**: Vanilla HTML5, CSS3, ES6+ JavaScript
- **Performance**: Numba (Just-In-Time Compilation), NumPy Vectorization
- **AI Engine**: Google GenAI SDK (`gemini-1.5-flash`)
- **Graphics**: Plotly.js
- **Data Handling**: Pandas, OpenPyXL

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Google Gemini API Key

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create `.env` in `misc/`:
```env
GEMINI_API_KEY=your_key
```

### 4. Launch
```bash
python main.py
```
Visit `http://localhost:8000`

---

## 📂 Project Architecture

```text
├── main.py               # FastAPI server
├── frontend/             # Clean HTML/CSS/JS frontend
├── core/                 # Modular Business Logic
│   ├── engine/           # JIT-Compiled Math & Simulations
│   ├── comparator/       # Portfolio Audit & Optimization
│   ├── parser/           # Data Ingestion (CSV/Excel)
│   ├── gen_ai/           # Gemini AI Insights
│   ├── data/             # Support Asset Universes
│   └── graph/            # Server-side Chart Definitions
├── misc/                 # Configurations & Audit Scripts
└── requirements.txt      # Optimized Dependencies
```

---

**Developed for the Major Project 2025.**
*Disclaimer: Educational use only. Financial calculations are projections based on historical data.*
