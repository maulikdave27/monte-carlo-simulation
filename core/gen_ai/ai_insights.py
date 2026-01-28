import os
from google import genai
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv("misc/.env")

def get_genai_client():
    """Configures the Gemini API Client with the key from .env"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, "⚠️ GEMINI_API_KEY not found in .env file."
    
    try:
        client = genai.Client(api_key=api_key)
        return client, ""
    except Exception as e:
        return None, f"⚠️ Error configuring Gemini Client: {str(e)}"

def get_simulation_insights(user_metrics, optimal_metrics, simulation_data, tickers):
    """
    Generates text insights using Gemini based on portfolio simulation data.
    
    Args:
        user_metrics (dict): {'return': float, 'volatility': float, 'sharpe': float, 'sortino': float, 'cvar': float, 'diversification_score': float, 'weights': list}
        optimal_metrics (dict): {'return': float, 'volatility': float, 'sharpe': float, 'sortino': float, 'cvar': float, 'diversification_score': float, 'weights': list}
        simulation_data (dict): {'returns': list, 'volatility': list, 'sharpe': list} - Raw sim data
        tickers (list): List of asset ticker symbols
        
    Returns:
        str: MARKDOWN formatted insights from Gemini.
    """
    
    # 1. Configure API
    client, msg = get_genai_client()
    if not client:
        return msg

    # 2. Compress Data (Calculate Aggregates)
    sim_returns = np.array(simulation_data['returns'])
    sim_vol = np.array(simulation_data['volatility'])
    sim_sharpe = np.array(simulation_data['sharpe'])
    
    stats = {
        "count": len(sim_returns),
        "return_min": np.min(sim_returns),
        "return_max": np.max(sim_returns),
        "return_mean": np.mean(sim_returns),
        "return_median": np.median(sim_returns),
        "vol_min": np.min(sim_vol),
        "vol_max": np.max(sim_vol),
        "sharpe_max": np.max(sim_sharpe),
        "sharpe_mean": np.mean(sim_sharpe),
    }
    
    # Better percentile calculation
    user_ret_pct = (sim_returns < user_metrics['return']).mean() * 100
    user_sharpe_pct = (sim_sharpe < user_metrics['sharpe']).mean() * 100
    user_sortino_pct = (np.array(simulation_data['sortino']) < user_metrics['sortino']).mean() * 100 if 'sortino' in simulation_data else 0
    
    # 3. Construct the Prompt
    prompt = f"""
    You are an expert financial analyst acting as an AI Portfolio Consultant.
    
    **Context:**
    We ran a Monte Carlo simulation with {stats['count']:,} iterations to find the optimal portfolio for a fixed set of assets.
    
    **Asset Universe:**
    {', '.join(tickers)}
    (Please infer the sector/industry exposures based on these tickers).
    
    **Market/Simulation Context (The "Possibility Space"):**
    - Returns Range: {stats['return_min']:.2%} to {stats['return_max']:.2%} (Median: {stats['return_median']:.2%})
    - Volatility Range: {stats['vol_min']:.2%} to {stats['vol_max']:.2%}
    - Max Possible Sharpe Ratio: {stats['sharpe_max']:.2f} (Average: {stats['sharpe_mean']:.2f})
    
    **User's Portfolio Performance:**
    - Return: {user_metrics['return']:.2%} (Better than {user_ret_pct:.1f}% of random portfolios)
    - Volatility: {user_metrics['volatility']:.2%}
    - Sharpe Ratio: {user_metrics['sharpe']:.2f} (Better than {user_sharpe_pct:.1f}% of random portfolios)
    - Sortino Ratio: {user_metrics['sortino']:.2f}
    - CVaR (95%): {user_metrics['cvar']:.2%} (Theoretical worst 5% loss)
    - Diversification Score: {user_metrics['diversification_score']:.0%} (Higher is better)
    - Allocations: {dict(zip(tickers, [round(w, 3) for w in user_metrics['weights']]))}
    
    **AI Optimized Portfolio:**
    - Return: {optimal_metrics['return']:.2%}
    - Volatility: {optimal_metrics['volatility']:.2%}
    - Sharpe Ratio: {optimal_metrics['sharpe']:.2f}
    - Sortino Ratio: {optimal_metrics['sortino']:.2f}
    - CVaR (95%): {optimal_metrics['cvar']:.2%}
    - Diversification Score: {optimal_metrics['diversification_score']:.0%}
    - Allocations: {dict(zip(tickers, [round(w, 3) for w in optimal_metrics['weights']]))}
    
    **Task:**
    Provide a professional, high-net-worth style analysis. The output MUST be in beautiful MARKDOWN format and follow this EXACT structure:

    ### SECTOR SUMMARY
    [A punchy 3-4 sentence summary of the portfolio's current sector-based exposure and the strategic shift recommended by the AI. Focus on sector concentrations and diversification.]

    ---SPLIT---

    ### DETAILED INSIGHTS
    #### Performance Analysis
    [Deep dive comparing User vs Optimal metrics. Discuss Risk vs Efficiency.]

    #### Detailed Sector Breakdown & Asset Strategy
    [A granular look at each sector involved. Explain why the AI moved weights between specific tickers/sectors. Use table or bullet points if appropriate.]

    #### Strategic Recommendation
    [Final professional verdict.]

    No "robot talk", no preamble, just the markdown report starting with ### SECTOR SUMMARY.
    """
    
    # 4. Call Model
    try:
        # Use the google-genai SDK syntax
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite', 
            contents=prompt
        )
        
        # Return the raw markdown text
        return response.text
            
    except Exception as e:
        return f"⚠️ **AI Error**: Error generating insight: {str(e)}"
