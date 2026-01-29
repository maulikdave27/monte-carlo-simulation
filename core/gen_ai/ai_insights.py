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

def generate_full_report(user_metrics, optimal_metrics, simulation_data, tickers, total_simulations=None):
    """
    Generates text insights using Gemini based on portfolio simulation data.
    
    Args:
        user_metrics (dict): {'return': float, 'volatility': float, 'sharpe': float, 'sortino': float, 'cvar': float, 'diversification_score': float, 'weights': list}
        optimal_metrics (dict): {'return': float, 'volatility': float, 'sharpe': float, 'sortino': float, 'cvar': float, 'diversification_score': float, 'weights': list}
        simulation_data (dict): {'returns': list, 'volatility': list, 'sharpe': list} - Raw sim data
        tickers (list): List of asset ticker symbols
        total_simulations (int, optional): The actual total number of iterations run (before sampling)
        
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
    display_count = total_simulations if total_simulations else stats['count']
    
    prompt = f"""
    You are an elite institutional Portfolio Strategist at a top-tier asset management firm.
    
    **Context:**
    We ran a Monte Carlo simulation with {display_count:,} iterations to find the optimal risk-adjusted portfolio.
    
    **Asset Universe:**
    {', '.join(tickers)}
    
    **Market/Simulation Context:**
    - Returns Range: {stats['return_min']:.2%} to {stats['return_max']:.2%} (Median: {stats['return_median']:.2%})
    - Volatility Range: {stats['vol_min']:.2%} to {stats['vol_max']:.2%}
    - Max Sharpe Ratio Achieved: {stats['sharpe_max']:.2f} (Average: {stats['sharpe_mean']:.2f})
    
    **User's Current Portfolio:**
    - Expected Return: {user_metrics['return']:.2%} (Ranks in top {100-user_ret_pct:.1f}% of simulations)
    - Volatility: {user_metrics['volatility']:.2%}
    - Sharpe Ratio: {user_metrics['sharpe']:.2f} (Ranks in top {100-user_sharpe_pct:.1f}% of simulations)
    - Sortino Ratio: {user_metrics['sortino']:.2f}
    - CVaR (95%): {user_metrics['cvar']:.2%}
    - Diversification Score: {user_metrics['diversification_score']:.0%}
    - Current Weights: {dict(zip(tickers, [round(w, 3) for w in user_metrics['weights']]))}
    
    **AI Optimized Portfolio:**
    - Expected Return: {optimal_metrics['return']:.2%}
    - Volatility: {optimal_metrics['volatility']:.2%}
    - Sharpe Ratio: {optimal_metrics['sharpe']:.2f}
    - Sortino Ratio: {optimal_metrics['sortino']:.2f}
    - CVaR (95%): {optimal_metrics['cvar']:.2%}
    - Diversification Score: {optimal_metrics['diversification_score']:.0%}
    - Optimal Weights: {dict(zip(tickers, [round(w, 3) for w in optimal_metrics['weights']]))}
    
    **Key Performance Improvements:**
    - Return Delta: {(optimal_metrics['return'] - user_metrics['return']):.2%}
    - Volatility Reduction: {(user_metrics['volatility'] - optimal_metrics['volatility']):.2%}
    - Sharpe Improvement: {(optimal_metrics['sharpe'] - user_metrics['sharpe']):.2f}
    - CVaR Improvement: {(user_metrics['cvar'] - optimal_metrics['cvar']):.2%}
    
    **Task:**
    Generate a COMPREHENSIVE, PROFESSIONALLY-STYLED investment report in beautiful Markdown format.
    This report will be converted to PDF for institutional clients.
    
    **Required Structure (Follow EXACTLY):**
    
    ## 📊 Executive Summary
    A compelling 4-5 sentence overview of the portfolio analysis findings. Highlight the key improvement opportunity and the strategic recommendation. Use authoritative language.
    
    ---
    
    ## 📈 Performance Analysis
    
    ### Current vs Optimal Comparison
    Create a detailed comparison table and narrative analysis of:
    - Risk-adjusted returns (Sharpe, Sortino)
    - Tail risk exposure (CVaR)
    - Diversification benefits
    - Volatility profile
    
    ### Simulation Context
    Explain where the portfolio ranks among {display_count:,} simulated portfolios.
    Discuss the statistical significance of the optimization.
    
    ---
    
    ## 🏢 Sector & Asset Strategy
    
    ### Sector Rotation Analysis
    Analyze the sector exposure shifts between current and optimal allocations.
    Explain the macroeconomic rationale for each major shift.
    
    ### Asset-Level Recommendations
    For each significant weight change, provide:
    - Current weight vs recommended weight
    - Rationale for the change
    - Expected impact on portfolio
    
    ---
    
    ## ⚠️ Risk Assessment
    
    ### Downside Protection
    Discuss CVaR improvements and what they mean in practical terms.
    Estimate potential dollar impact on a $1M portfolio in worst-case scenarios.
    
    ### Volatility Analysis
    Compare current vs optimal volatility profiles.
    Discuss trade-offs between return and stability.
    
    ---
    
    ## 🎯 Strategic Recommendations
    
    Provide 3-5 specific, actionable recommendations for the investor.
    Use bullet points with bold action items.
    Be direct and prescriptive - this is for sophisticated institutional clients.
    
    ---
    
    ## 📋 Conclusion
    A strong 2-3 sentence closing that reinforces the key message.
    
    **Formatting Guidelines:**
    - Use proper Markdown headers (##, ###)
    - Include horizontal rules (---) between major sections
    - Use **bold** for emphasis on key metrics
    - Use bullet points for lists
    - Professional, authoritative tone throughout
    - No "I think" or "We suggest" - use "The analysis indicates", "The portfolio requires"
    - Minimum 800 words total
    """
    
    # 4. Call Model
    try:
        # Use the google-genai SDK syntax
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        
        # Return the raw markdown text
        return response.text
            
    except Exception as e:
        return f"⚠️ **AI Error**: Error generating insight: {str(e)}"
