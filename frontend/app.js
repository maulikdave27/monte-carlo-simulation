// --- Global State ---
let currentResults = null;

// --- Event Listeners ---
document.addEventListener('DOMContentLoaded', () => {

    // Slider Sync
    const slider = document.getElementById('numSimulations');
    if (slider) {
        slider.addEventListener('input', (e) => {
            document.getElementById('simValue').textContent = parseInt(e.target.value).toLocaleString();
        });
    }

    // Input Method Toggle
    const radioButtons = document.querySelectorAll('input[name="inputMethod"]');
    radioButtons.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const val = e.target.value;
            const fileSection = document.getElementById('fileUploadSection');
            const manualSection = document.getElementById('manualInputSection');

            if (val === 'upload') {
                fileSection.classList.remove('hidden');
                manualSection.classList.add('hidden');
            } else {
                fileSection.classList.add('hidden');
                manualSection.classList.remove('hidden');
            }
        });
    });

    // Form Submission
    const form = document.getElementById('auditForm');
    form.addEventListener('submit', handleAuditSubmit);

    // AI Button
    const aiBtn = document.getElementById('askAiBtn');
    aiBtn.addEventListener('click', handleAiRequest);
});

// --- Tab Logic ---
function showTab(tabId) {
    // Hide all contents
    document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
    // Remove active class from buttons
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    // Show target
    document.getElementById(tabId + 'Tab').classList.remove('hidden');
    // Set active button
    event.currentTarget.classList.add('active');

    // Trigger resize for Plotly
    window.dispatchEvent(new Event('resize'));
}

// --- Handlers ---

async function handleAuditSubmit(e) {
    e.preventDefault();
    const submitBtn = document.getElementById('runBtn');
    submitBtn.textContent = 'Running...';
    submitBtn.disabled = true;

    try {
        const formData = new FormData(e.target);
        const inputMethod = formData.get('inputMethod');

        let payload = {
            time_horizon: formData.get('timeHorizon'),
            risk_preference: formData.get('riskPreference'),
            num_simulations: parseInt(formData.get('numSimulations'))
        };

        if (inputMethod === 'upload') {
            const fileInput = document.getElementById('portfolioFile');
            if (fileInput.files.length === 0) {
                alert("Please select a file.");
                return;
            }
            // First Upload to get parsed data
            const uploadData = new FormData();
            uploadData.append('file', fileInput.files[0]);

            const uploadRes = await fetch('/api/upload', {
                method: 'POST',
                body: uploadData
            });

            if (!uploadRes.ok) throw new Error("Upload Failed");
            const parsed = await uploadRes.json();

            payload.tickers = parsed.tickers;
            payload.weights = parsed.weights;

        } else {
            // Manual Test Payload
            payload.tickers = ["AAPL", "JPM", "XOM", "NVDA", "MSFT", "GOOGL", "AMZN"];
            payload.weights = Array(7).fill(1 / 7); // Equal weight
        }

        // Run Audit
        const res = await fetch('/api/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Audit Failed");
        }

        const data = await res.json();
        currentResults = data; // Store for AI

        // Render
        renderDashboard(data);

    } catch (error) {
        alert(error.message);
        console.error(error);
    } finally {
        submitBtn.textContent = 'Run Risk Analysis';
        submitBtn.disabled = false;
    }
}

async function handleAiRequest() {
    if (!currentResults) return;

    const aiBtn = document.getElementById('askAiBtn');
    const responseDiv = document.getElementById('aiResponse');

    aiBtn.textContent = 'Consulting AI...';
    aiBtn.disabled = true;

    try {
        const payload = {
            user_metrics: currentResults.user,
            optimal_metrics: currentResults.optimal,
            simulation_data: currentResults.summary_data,
            tickers: currentResults.tickers
        };

        const res = await fetch('/api/insights', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("AI Request Failed");

        const data = await res.json();

        // Render Markdown
        responseDiv.innerHTML = marked.parse(data.markdown);
        responseDiv.classList.remove('hidden');

    } catch (error) {
        alert("AI Error: " + error.message);
    } finally {
        aiBtn.textContent = '✨ Ask AI Specialist';
        aiBtn.disabled = false;
    }
}

// --- Rendering Logic ---

function renderDashboard(data) {
    document.getElementById('resultsDashboard').classList.remove('hidden');

    // 1. Metrics
    document.getElementById('userMetrics').innerHTML = generateMetricHTML(data.user);
    document.getElementById('optimalMetrics').innerHTML = generateMetricHTML(data.optimal, data.user);

    // 2. Charts
    renderFrontierChart(data.summary_data, data.user, data.optimal);
    renderAllocationCharts(data.tickers, data.user.weights, data.optimal.weights);
    renderSectorChart(data.sector_data);
}

function generateMetricHTML(m, compare = null) {
    const getDelta = (val, compVal, isPercent = true, inverse = false) => {
        if (compVal === null || compVal === undefined) return '';
        const diff = val - compVal;
        const cls = diff > 0 ? (inverse ? 'down' : 'up') : (inverse ? 'up' : 'down');
        const sign = diff > 0 ? '+' : '';

        let fmt;
        if (isPercent) {
            fmt = (diff * 100).toFixed(2) + '%';
        } else {
            fmt = diff.toFixed(2);
        }

        return `<span class="delta ${cls}">(${sign}${fmt})</span>`;
    };

    return `
        <div class="metric-item"><span>Return:</span> <strong>${(m.return * 100).toFixed(2)}%</strong> ${compare ? getDelta(m.return, compare.return, true) : ''}</div>
        <div class="metric-item"><span>Risk:</span> <strong>${(m.volatility * 100).toFixed(2)}%</strong> ${compare ? getDelta(m.volatility, compare.volatility, true, true) : ''}</div>
        <div class="metric-item"><span>Sharpe:</span> <strong>${m.sharpe.toFixed(2)}</strong> ${compare ? getDelta(m.sharpe, compare.sharpe, false) : ''}</div>
        <div class="metric-item"><span>Sortino:</span> <strong>${m.sortino.toFixed(2)}</strong> ${compare ? getDelta(m.sortino, compare.sortino, false) : ''}</div>
        <div class="metric-item"><span>CVaR (95%):</span> <strong>${(m.cvar * 100).toFixed(2)}%</strong> ${compare ? getDelta(m.cvar, compare.cvar, true, true) : ''}</div>
        <div class="metric-item"><span>Stress Drawdown:</span> <strong>${(m.stress_drawdown * 100).toFixed(2)}%</strong> ${compare ? getDelta(m.stress_drawdown, compare.stress_drawdown, true, true) : ''}</div>
        <div class="metric-item"><span>Diversification:</span> <strong>${(m.diversification_score * 100).toFixed(0)}%</strong> ${compare ? getDelta(m.diversification_score, compare.diversification_score, true) : ''}</div>
    `;
}

function renderFrontierChart(simData, user, optimal) {
    const traceSim = {
        x: simData.volatility,
        y: simData.returns,
        mode: 'markers',
        type: 'scatter',
        name: 'Simulations',
        marker: { color: '#e0e0e0', size: 3, opacity: 0.5 }
    };

    const traceUser = {
        x: [user.volatility],
        y: [user.return],
        mode: 'markers+text',
        type: 'scatter',
        name: 'You',
        text: ['YOU'],
        textposition: 'top center',
        marker: { color: 'red', size: 14, symbol: 'x' }
    };

    const traceOpt = {
        x: [optimal.volatility],
        y: [optimal.return],
        mode: 'markers+text',
        type: 'scatter',
        name: 'Optimal',
        text: ['AI'],
        textposition: 'top center',
        marker: { color: 'green', size: 14, symbol: 'star' }
    };

    Plotly.newPlot('frontierChart', [traceSim, traceUser, traceOpt], {
        margin: { t: 40, l: 60, r: 40, b: 60 },
        xaxis: { title: 'Annual Risk (Volatility)', tickformat: '.1%' },
        yaxis: { title: 'Expected Annual Return', tickformat: '.1%' },
        showlegend: false,
        hovermode: 'closest'
    });
}

function renderAllocationCharts(tickers, userWeights, optWeights) {
    const userTrace = {
        labels: tickers,
        values: userWeights,
        type: 'pie',
        hole: .4,
        name: 'User'
    };

    const optTrace = {
        labels: tickers,
        values: optWeights,
        type: 'pie',
        hole: .4,
        name: 'Optimal'
    };

    Plotly.newPlot('userAllocationChart', [userTrace], { margin: { t: 20, b: 20, l: 20, r: 20 } });
    Plotly.newPlot('optimalAllocationChart', [optTrace], { margin: { t: 20, b: 20, l: 20, r: 20 } });
}

function renderSectorChart(sectorData) {
    const sectors = Object.keys(sectorData.user).concat(Object.keys(sectorData.optimal))
        .filter((v, i, a) => a.indexOf(v) === i).sort();

    const userVals = sectors.map(s => sectorData.user[s] || 0);
    const optVals = sectors.map(s => sectorData.optimal[s] || 0);

    const traceUser = {
        x: sectors,
        y: userVals,
        name: 'Your Portfolio',
        type: 'bar',
        marker: { color: 'indianred' }
    };

    const traceOpt = {
        x: sectors,
        y: optVals,
        name: 'AI Optimized',
        type: 'bar',
        marker: { color: 'lightseagreen' }
    };

    Plotly.newPlot('sectorChart', [traceUser, traceOpt], {
        barmode: 'group',
        margin: { t: 40, l: 60, r: 40, b: 100 },
        yaxis: { tickformat: '.1%' },
        xaxis: { tickangle: -45 }
    });
}
