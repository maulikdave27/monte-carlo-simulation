from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import pandas as pd
import io
import json
import numpy as np

# Import Core Logic
from core.parser import excel_parser
from core.comparator import portfolio_audit
from core.gen_ai import ai_insights
from core.data import universe
from core.graph import chart_generator
from dotenv import load_dotenv

# Load Env
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
    simulation_data: Dict # Simplified stats
    tickers: List[str]

# --- API Endpoints ---

@app.get("/")
def read_root():
    from fastapi.responses import FileResponse
    return FileResponse('frontend/index.html')

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Parses an uploaded portfolio file (CSV/Excel)"""
    try:
        content = await file.read()
        file_obj = io.BytesIO(content)
        file_obj.name = file.filename 
        
        df, error = excel_parser.parse_portfolio(file_obj)
        if error:
            raise HTTPException(status_code=400, detail=error)
            
        return {
            "tickers": df['Ticker'].tolist(),
            "weights": df['Weight'].tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/audit")
def run_audit_endpoint(request: AuditRequest):
    """Runs the full portfolio risk simulation"""
    try:
        # 1. Reconstruct User Portfolio
        user_df = pd.DataFrame({'Ticker': request.tickers, 'Weight': request.weights})
        
        # 2. Optimized Data Loading (No background caching as requested)
        data_path = "core/data/daily_returns.csv"
        # Using engine='c' for maximum speed without external dependencies like pyarrow
        hist_data = pd.read_csv(data_path, index_col=0, parse_dates=True, engine='c')
        
        # 3. Parameter Mapping
        risk_free_map = {"1-3 years": 0.015, "3-6 years": 0.02, "6+ years": 0.025}
        rf_rate = risk_free_map.get(request.time_horizon, 0.02)

        # 4. Run Audit Synchronously (JIT is fast enough)
        result, err = portfolio_audit.run_audit(
            user_df,
            hist_data,
            risk_preference=request.risk_preference,
            risk_free_rate=rf_rate,
            num_simulations=request.num_simulations,
            time_horizon=request.time_horizon
        )
        
        if err:
            raise HTTPException(status_code=400, detail=err)
            
        # 5. Efficient Response Building (Only downsample what's needed)
        # Avoid TO_LIST on 2M items!
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

        response = {
            "user": result['user'],
            "optimal": result['optimal'],
            "tickers": result['tickers'],
            "summary_data": summary_data,
            "sector_data": {"user": user_sectors, "optimal": opt_sectors}
        }
        
        def convert_numpy(obj):
            if isinstance(obj, (np.integer, np.floating)): return float(obj)
            if isinstance(obj, np.ndarray): return obj.tolist()
            return obj

        return json.loads(json.dumps(response, default=convert_numpy))

    except Exception as e:
        print(f"Audit Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

import traceback

@app.post("/api/insights")
def get_insights(request: InsightRequest):
    """Calls Gemini for AI analysis"""
    try:
        analysis = ai_insights.get_simulation_insights(
            user_metrics=request.user_metrics,
            optimal_metrics=request.optimal_metrics,
            simulation_data=request.simulation_data,
            tickers=request.tickers
        )
        return {"markdown": analysis}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
