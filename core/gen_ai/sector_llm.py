import ollama

def analyze_sector_rotation(
    user_sectors, optimal_sectors, risk_pref,
    user_metrics=None, optimal_metrics=None,
    sector_risk_contrib=None, tickers=None
):
    """
    Uses Ollama (Gemma 3 4B) to provide rich, actionable portfolio insights.
    Accepts additional portfolio data for more specific recommendations.
    """
    
    # Build metrics comparison table if available
    metrics_section = ""
    if user_metrics and optimal_metrics:
        metrics_section = f"""
### Performance Metrics
| Metric | Current | Optimal | Gap |
|--------|---------|---------|-----|
| Annual Return | {user_metrics.get('return', 'N/A')}% | {optimal_metrics.get('return', 'N/A')}% | {round(optimal_metrics.get('return', 0) - user_metrics.get('return', 0), 2)}% |
| Volatility | {user_metrics.get('volatility', 'N/A')}% | {optimal_metrics.get('volatility', 'N/A')}% | {round(optimal_metrics.get('volatility', 0) - user_metrics.get('volatility', 0), 2)}% |
| Sharpe Ratio | {user_metrics.get('sharpe', 'N/A')} | {optimal_metrics.get('sharpe', 'N/A')} | {round(optimal_metrics.get('sharpe', 0) - user_metrics.get('sharpe', 0), 2)} |
| Sortino Ratio | {user_metrics.get('sortino', 'N/A')} | {optimal_metrics.get('sortino', 'N/A')} | {round(optimal_metrics.get('sortino', 0) - user_metrics.get('sortino', 0), 2)} |
"""

    # Build risk decomposition section if available
    risk_section = ""
    if sector_risk_contrib:
        risk_items = [f"- {k}: {v:.1f}%" for k, v in sector_risk_contrib.items()]
        risk_section = f"""
### Risk Decomposition (Sector Contribution to Portfolio Volatility)
{chr(10).join(risk_items)}
"""

    # Build tickers section if available
    tickers_section = ""
    if tickers:
        tickers_section = f"""
### Holdings
Tickers in portfolio: {', '.join(tickers)}
"""

    # Format sector allocations nicely
    user_sector_str = ", ".join([f"{k}: {v:.1f}%" for k, v in user_sectors.items()])
    opt_sector_str = ", ".join([f"{k}: {v:.1f}%" for k, v in optimal_sectors.items()])

    prompt = f"""You are a Senior Portfolio Strategist specializing in Tactical Asset Allocation. 

## Portfolio Context
{tickers_section}
{metrics_section}
### Current vs. Optimal Allocation
- Current: {user_sector_str}
- Optimal: {opt_sector_str}
{risk_section}
### Strategy Constraint
Target Risk Profile: {risk_pref}

---

## Technical Directive
Deliver a high-density **Sector Rotation Analysis** in exactly 6 insights. You must use the provided metrics (Sharpe, Volatility, Risk %) to justify every recommendation. Be professional, quantitative, and direct.

Format your response EXACTLY like this:

### 🔄 Sector Rotation Analysis
* [Insight 1: Quantitative audit of current risk/return efficiency vs optimal frontier]
* [Insight 2: Analysis of sector concentration risk and diversification quality]

### 🎯 Strategic Rebalancing
* [Insight 3: High-conviction sector rotation - Specify sector, target weight shift, and metric-based rationale]
* [Insight 4: Portfolio de-risking - Specify sector to trim, target reduction, and risk mitigation rationale]

### 🛡️ Tactical Risk Management
* [Insight 5: Critical volatility driver - reference sector risk contribution %]
* [Insight 6: Optimization outlook - how this shift aligns with the {risk_pref} mandate]

STRICT CONSTRAINTS:
1. ONLY return Markdown. No intro/outro.
2. Exactly 6 bullet points total.
3. Max 30 words per point.
4. Reference SPECIFIC NUMBERS from the data (e.g., "Increase Tech from 12% to 18%").
5. Use professional financial terminology.
"""
    
    try:
        response = ollama.chat(
            model='gemma3:4b',
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.1}  # More focused, consistent outputs
        )
        content = response['message']['content'].strip()
        
        # Clean up in case AI adds extra backticks or intro
        if '```' in content:
            parts = content.split('```')
            if len(parts) >= 2:
                content = parts[1]
                if content.startswith('markdown'):
                    content = content[8:]
        
        return content.strip()
    except Exception as e:
        return f"### ⚠️ Error\nConnection failed: {str(e)}"
