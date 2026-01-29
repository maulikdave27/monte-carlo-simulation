import os
import uvicorn
import pandas as pd
import numpy as np
import io
import json
from typing import List, Dict, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Import Core Logic
from core.parser import excel_parser
from core.comparator import portfolio_audit
from core.gen_ai import ai_insights
from core.data import universe
from core.graph import chart_generator

# --- 1. OPTIMIZATION & CACHING ---
os.environ['NUMBA_THREAD_POOL_SIZE'] = '4'
os.environ['NUMBA_THREADING_LAYER'] = 'workqueue' 

HIST_DATA = None

def load_global_data():
    global HIST_DATA
    if HIST_DATA is None:
        try:
            print(">>> CACHING UNIVERSE DATA...")
            data_path = "core/data/daily_returns.csv"
            HIST_DATA = pd.read_csv(data_path, index_col=0, parse_dates=True, engine='c')
            print(f">>> CACHED {len(HIST_DATA.columns)} TICKERS.")
        except Exception as e:
            print(f">>> CACHE FAILED: {e}")

load_global_data()

# --- 2. FASTAPI SETUP ---
load_dotenv("misc/.env")
app = FastAPI(title="Portfolio Risk Intelligence API")

# Mount Frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# --- Pydantic Models for Input ---
class AuditRequest(BaseModel):
    tickers: List[str]
    weights: List[float]
    time_horizon: str = "3-6 years"
    risk_preference: str = "Medium"
    num_simulations: int = 1000000

class InsightRequest(BaseModel):
    user_metrics: Dict
    optimal_metrics: Dict
    simulation_data: Dict
    tickers: List[str]
    total_simulations: Optional[int] = None

# --- API Endpoints ---

@app.get("/")
def read_root():
    from fastapi.responses import FileResponse
    return FileResponse('frontend/index.html')

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_obj = io.BytesIO(content)
        file_obj.name = file.filename 
        df, error = excel_parser.parse_portfolio(file_obj)
        if error: raise HTTPException(status_code=400, detail=error)
        return {"tickers": df['Ticker'].tolist(), "weights": df['Weight'].tolist()}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/audit")
def run_audit_endpoint(request: AuditRequest):
    try:
        global HIST_DATA
        if HIST_DATA is None: load_global_data()
        
        user_df = pd.DataFrame({'Ticker': request.tickers, 'Weight': request.weights})
        user_tickers = user_df['Ticker'].tolist()
        valid_tickers = [t for t in user_tickers if t in HIST_DATA.columns]
        missing = set(user_tickers) - set(valid_tickers)
        
        if len(valid_tickers) < 7:
            msg = f"Incomplete Portfolio. Found {len(valid_tickers)} supported stocks, need 7+."
            if missing: msg += f" Missing: {', '.join(list(missing)[:5])}"
            raise HTTPException(status_code=400, detail=msg)

        risk_free_map = {"1-3 years": 0.015, "3-6 years": 0.02, "6+ years": 0.025}
        rf_rate = risk_free_map.get(request.time_horizon, 0.02)

        result, err = portfolio_audit.run_audit(
            user_df, HIST_DATA,
            risk_preference=request.risk_preference,
            risk_free_rate=rf_rate,
            num_simulations=request.num_simulations,
            time_horizon=request.time_horizon
        )
        if err: raise HTTPException(status_code=400, detail=err)
            
        user_sectors = universe.get_sector_weights(result['tickers'], result['user']['weights'])
        opt_sectors = universe.get_sector_weights(result['tickers'], result['optimal']['weights'])
        
        sim_data = result['simulation_data']
        n_points = min(len(sim_data['returns']), 10000)
        idx = np.random.choice(len(sim_data['returns']), n_points, replace=False)
        
        summary_data = {
            "returns": sim_data['returns'][idx].tolist(),
            "volatility": sim_data['volatility'][idx].tolist(),
            "sharpe": sim_data['sharpe'][idx].tolist(),
            "sortino": sim_data['sortino'][idx].tolist()
        }

        # Calculate Correlation Matrix & Volatility Contribution
        subset_prices = HIST_DATA[result['tickers']]
        subset_returns = subset_prices.pct_change().dropna()
        
        # 1. Correlation
        corr_matrix = subset_returns.corr().round(2)
        corr_data = {
            "labels": result['tickers'],
            "matrix": corr_matrix.values.tolist()
        }

        # 2. Sector-wise Risk Decomposition (Percentage Contribution)
        # Use the covariance matrix from portfolio_audit (already annualized and clean)
        w = np.array(result['optimal']['weights'])
        cov_matrix = result['cov_matrix']  # Use the pre-calculated clean cov matrix
        
        # Calculate portfolio variance and risk contribution
        cov_w = cov_matrix @ w
        port_variance = float(w @ cov_w)
        
        print(f">>> DEBUG VOL: weights sum = {np.sum(w):.4f}, port_variance = {port_variance:.6f}")
        
        if port_variance > 1e-10 and not np.isnan(port_variance):
            # Risk contribution per asset
            risk_contrib = w * cov_w
            # As percentage of total variance (sums to 100%)
            pct_contrib = (risk_contrib / port_variance) * 100
            print(f">>> DEBUG VOL: pct_contrib sum = {np.sum(pct_contrib):.2f}%")
        else:
            print(">>> DEBUG VOL: Invalid port_variance, using equal distribution")
            # Fallback: distribute by weight
            pct_contrib = w * 100
            
        # Aggregate by sector
        sector_results = {}
        for i, ticker in enumerate(result['tickers']):
            sector = universe.get_ticker_sector(ticker.upper())
            sector_results[sector] = sector_results.get(sector, 0.0) + float(pct_contrib[i])
        
        print(f">>> DEBUG VOL: sector_results = {sector_results}")
            
        # Remove negligible "Other" sector
        if "Other" in sector_results and len(sector_results) > 1 and sector_results["Other"] < 0.1:
            del sector_results["Other"]

        # Sort by contribution (highest first)
        sorted_impact = dict(sorted(sector_results.items(), key=lambda x: x[1], reverse=True))
        
        actv_data = {
            "labels": list(sorted_impact.keys()),
            "values": [round(float(v), 2) for v in sorted_impact.values()]
        }
        print(f">>> DEBUG VOL: actv_data = {actv_data}")

        # 3. Rolling Volatility Comparison (30-day rolling window)
        user_weights = np.array(result['user']['weights'])
        opt_weights = np.array(result['optimal']['weights'])
        
        # Calculate daily portfolio returns
        user_portfolio_returns = subset_returns @ user_weights
        opt_portfolio_returns = subset_returns @ opt_weights
        
        # Calculate 30-day rolling volatility (annualized)
        rolling_window = 30
        user_rolling_vol = user_portfolio_returns.rolling(window=rolling_window).std() * np.sqrt(252) * 100
        opt_rolling_vol = opt_portfolio_returns.rolling(window=rolling_window).std() * np.sqrt(252) * 100
        
        # Get dates and drop NaN values
        valid_idx = user_rolling_vol.dropna().index
        dates = [d.strftime('%Y-%m-%d') for d in valid_idx]
        user_vol_values = user_rolling_vol.dropna().values.tolist()
        opt_vol_values = opt_rolling_vol.dropna().values.tolist()
        
        # Sample data points if too many (keep ~100 points for smooth chart)
        max_points = 100
        if len(dates) > max_points:
            step = len(dates) // max_points
            dates = dates[::step]
            user_vol_values = user_vol_values[::step]
            opt_vol_values = opt_vol_values[::step]
        
        rolling_vol_data = {
            "dates": dates,
            "user": [round(v, 2) for v in user_vol_values],
            "optimal": [round(v, 2) for v in opt_vol_values]
        }

        response = {
            "user": result['user'], "optimal": result['optimal'],
            "tickers": result['tickers'], "summary_data": summary_data,
            "sector_data": {"user": user_sectors, "optimal": opt_sectors},
            "correlation": corr_data,
            "volatility_contribution": actv_data,
            "rolling_volatility": rolling_vol_data
        }
        
        def convert_numpy(obj):
            if isinstance(obj, (np.integer, np.floating)): return float(obj)
            if isinstance(obj, np.ndarray): return obj.tolist()
            if isinstance(obj, dict): return {k: convert_numpy(v) for k, v in obj.items()}
            if isinstance(obj, list): return [convert_numpy(v) for v in obj]
            return obj

        return JSONResponse(content=convert_numpy(response))
    except HTTPException: raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

import traceback
from fastapi.responses import StreamingResponse
from core.gen_ai import sector_llm
from core.report import pdf_generator

from typing import List, Dict, Optional, Any

class SectorRequest(BaseModel):
    user_sectors: Dict[str, float]
    optimal_sectors: Dict[str, float]
    risk_preference: str
    user_metrics: Optional[Dict[str, Any]] = None
    optimal_metrics: Optional[Dict[str, Any]] = None
    sector_risk_contrib: Optional[Dict[str, float]] = None
    tickers: Optional[List[str]] = None

class PDFRequest(BaseModel):
    markdown_text: str

@app.post("/api/sector-analysis")
async def get_sector_analysis(request: SectorRequest):
    try:
        analysis = sector_llm.analyze_sector_rotation(
            request.user_sectors,
            request.optimal_sectors,
            request.risk_preference,
            user_metrics=request.user_metrics,
            optimal_metrics=request.optimal_metrics,
            sector_risk_contrib=request.sector_risk_contrib,
            tickers=request.tickers
        )
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/insights")
async def get_ai_insights(request: InsightRequest):
    try:
        markdown = ai_insights.generate_full_report(
            request.user_metrics,
            request.optimal_metrics,
            request.simulation_data,
            request.tickers,
            total_simulations=request.total_simulations
        )
        return {"markdown": markdown}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import Response
from datetime import datetime

@app.post("/api/report/pdf")
async def get_pdf_report(request: PDFRequest):
    try:
        pdf_buffer = pdf_generator.create_pdf_report(request.markdown_text)
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Portfolio_Risk_Report_{timestamp}.pdf"
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
