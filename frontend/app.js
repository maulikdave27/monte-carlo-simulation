// APP.JS - Titanium V2.0 Logic (Refactored for Performance)
let appState = {
    results: null,
    chartInstance: null,
    stockPieUser: null,
    stockPieOpt: null,
    sectorPieUser: null,
    sectorPieOpt: null,
    lastMarkdown: null
};

const ui = {
    uploadInput: document.getElementById('portfolio-upload'),
    uploadZone: document.getElementById('upload-zone'),
    preview: document.getElementById('portfolio-preview'),
    tickerList: document.getElementById('ticker-list'),
    runBtn: document.getElementById('run-btn'),
    scorecards: document.getElementById('scorecards'),
    gauges: document.getElementById('sector-gauges'),

    // AI & Stock UI Elements
    fabAi: document.getElementById('fab-ai'),
    aiReportSection: document.getElementById('ai-report-section'),
    aiFullContent: document.getElementById('ai-full-content'),
    btnDownloadPdf: document.getElementById('btn-download-pdf'),
    btnAnalyzeSector: document.getElementById('btn-analyze-sector'),
    sectorAnalysisRes: document.getElementById('sector-analysis-result'),
    stockTableBody: document.getElementById('stock-table-body'),

    // Metrics
    vals: {
        retCurr: document.getElementById('val-ret-curr'),
        retOpt: document.getElementById('val-ret-opt'),
        retDelta: document.getElementById('val-ret-delta'),
        volCurr: document.getElementById('val-vol-curr'),
        volOpt: document.getElementById('val-vol-opt'),
        volDelta: document.getElementById('val-vol-delta'),
        shpCurr: document.getElementById('val-shp-curr'),
        shpOpt: document.getElementById('val-shp-opt'),
        shpDelta: document.getElementById('val-shp-delta'),
        sorCurr: document.getElementById('val-sor-curr'),
        sorOpt: document.getElementById('val-sor-opt'),
        sorDelta: document.getElementById('val-sor-delta'),
        cvarCurr: document.getElementById('val-cvar-curr'),
        cvarOpt: document.getElementById('val-cvar-opt'),
        cvarDelta: document.getElementById('val-cvar-delta'),
        ddCurr: document.getElementById('val-dd-curr'),
        ddOpt: document.getElementById('val-dd-opt'),
        ddDelta: document.getElementById('val-dd-delta'),
    }
};

document.addEventListener('DOMContentLoaded', () => {
    initChart();

    // Sidebar Toggle
    document.getElementById('toggle-sidebar').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('sidebar-collapsed');
    });
});

// --- CORE HANDLERS ---

ui.uploadInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    ui.uploadZone.classList.add('animate-pulse');
    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.tickers) {
            appState.tickers = data.tickers;
            appState.weights = data.weights;
            updatePreview(data.tickers);
            ui.runBtn.disabled = false;
        }
    } catch (err) { alert('Upload Failed'); }
    finally { ui.uploadZone.classList.remove('animate-pulse'); }
});

ui.runBtn.addEventListener('click', async () => {
    setLoading(true);
    const timeHorizon = document.querySelector('input[name="time_horizon"]:checked').value;
    const riskPref = document.querySelector('input[name="risk"]:checked').value;
    const sims = parseInt(document.querySelector('input[name="sims"]:checked').value);

    try {
        const res = await fetch('/api/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tickers: appState.tickers,
                weights: appState.weights,
                time_horizon: timeHorizon,
                risk_preference: riskPref,
                num_simulations: sims
            })
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'Simulation error');
        }

        appState.results = data;
        renderResults(data);
        ui.fabAi.classList.remove('hidden');
        ui.aiReportSection.classList.add('hidden');
        ui.sectorAnalysisRes.innerHTML = '<p class="opacity-50 italic text-center mt-4">Click center button to generate <br>local AI sector insights.</p>';
    } catch (err) {
        alert('Simulation Failed: ' + err.message);
        ui.fabAi.classList.add('hidden');
    } finally { setLoading(false); }
});

// AI Manual Button (Gemma 3)
ui.btnAnalyzeSector.addEventListener('click', generateSectorInsights);

async function generateSectorInsights() {
    ui.sectorAnalysisRes.innerHTML = '<div class="flex flex-col items-center justify-center p-4"><span class="spinner size-6 mb-2"></span><span class="text-accent text-[10px] animate-pulse">Running Gemma 3...</span></div>';
    try {
        // Format volatility contribution for the LLM
        const volContrib = {};
        if (appState.results.volatility_contribution) {
            const labels = appState.results.volatility_contribution.labels;
            const values = appState.results.volatility_contribution.values;
            labels.forEach((label, i) => { volContrib[label] = values[i]; });
        }

        const res = await fetch('/api/sector-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_sectors: appState.results.sector_data.user,
                optimal_sectors: appState.results.sector_data.optimal,
                risk_preference: document.querySelector('input[name="risk"]:checked').value,
                user_metrics: appState.results.user,
                optimal_metrics: appState.results.optimal,
                sector_risk_contrib: volContrib,
                tickers: appState.results.tickers
            })
        });
        const data = await res.json();
        ui.sectorAnalysisRes.innerHTML = marked.parse(data.analysis);
    } catch (err) { ui.sectorAnalysisRes.innerHTML = "<span class='text-red-500'>Ollama Connection Failed</span>"; }
}

// AI Summary Report (Gemini FAB)
ui.fabAi.addEventListener('click', async () => {
    ui.aiReportSection.classList.remove('hidden');
    ui.aiReportSection.scrollIntoView({ behavior: 'smooth' });
    ui.aiFullContent.innerHTML = '<div class="flex flex-col items-center justify-center p-12"><div class="spinner mb-4"></div><p class="text-xs text-slate-500">Generating AI Summary Report...</p></div>';

    try {
        const res = await fetch('/api/insights', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_metrics: appState.results.user,
                optimal_metrics: appState.results.optimal,
                simulation_data: appState.results.summary_data,
                tickers: appState.results.tickers
            })
        });
        const data = await res.json();
        ui.aiFullContent.innerHTML = marked.parse(data.markdown);
        ui.btnDownloadPdf.disabled = false;
        appState.lastMarkdown = data.markdown;
    } catch (err) { ui.aiFullContent.innerHTML = "<p class='text-red-500'>Report Generation Failed</p>"; }
});

ui.btnDownloadPdf.addEventListener('click', async () => {
    if (!appState.lastMarkdown) return;
    const res = await fetch('/api/report/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ markdown_text: appState.lastMarkdown })
    });
    if (res.ok) {
        const blob = await res.blob();

        // Generate proper filename with timestamp
        const now = new Date();
        const timestamp = now.getFullYear().toString() +
            String(now.getMonth() + 1).padStart(2, '0') +
            String(now.getDate()).padStart(2, '0') + '_' +
            String(now.getHours()).padStart(2, '0') +
            String(now.getMinutes()).padStart(2, '0') +
            String(now.getSeconds()).padStart(2, '0');
        const filename = `Portfolio_Risk_Report_${timestamp}.pdf`;

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
});



// --- RENDER HELPERS ---

function updatePreview(tickers) {
    ui.preview.classList.remove('hidden');
    document.getElementById('asset-count').textContent = tickers.length;
    ui.tickerList.innerHTML = tickers.map(t => `<span class="text-[9px] font-mono bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded">${t}</span>`).join('');
}

function setLoading(isLoading) {
    ui.runBtn.disabled = isLoading;
    ui.runBtn.innerHTML = isLoading ? '<div class="spinner"></div> PROCESSING...' : '<span class="material-symbols-outlined text-lg group-hover:animate-pulse">bolt</span> RUN SIMULATION';
}

function renderResults(data) {
    const user = data.user;
    const opt = data.optimal;
    const fmtP = (n) => (n * 100).toFixed(1) + '%';
    const fmtN = (n) => n.toFixed(2);

    const setBadge = (id, current, optimal, isHigherBetter = true, isPercent = true) => {
        const el = document.getElementById(id);
        const parent = el.parentElement;
        const diff = optimal - current;
        const isPositive = isHigherBetter ? diff > 0 : diff < 0;
        let txt = isPercent ? (diff * 100).toFixed(1) + '%' : diff.toFixed(2);
        if (diff > 0) txt = '+' + txt;
        parent.className = "flex items-center gap-1 px-2 py-1 rounded text-xs font-mono font-bold " + (isPositive ? "bg-accent/10 text-accent border border-accent/20" : "bg-red-500/10 text-red-400 border border-red-500/20");
        el.innerHTML = `${isPositive ? (isHigherBetter ? '▲' : '▼') : (isHigherBetter ? '▼' : '▲')} ${txt}`;
    };

    ui.vals.retCurr.textContent = fmtP(user.return);
    ui.vals.retOpt.textContent = fmtP(opt.return);
    setBadge('val-ret-delta', user.return, opt.return, true, true);

    ui.vals.volCurr.textContent = fmtP(user.volatility);
    ui.vals.volOpt.textContent = fmtP(opt.volatility);
    setBadge('val-vol-delta', user.volatility, opt.volatility, false, true);

    ui.vals.shpCurr.textContent = fmtN(user.sharpe);
    ui.vals.shpOpt.textContent = fmtN(opt.sharpe);
    setBadge('val-shp-delta', user.sharpe, opt.sharpe, true, false);

    ui.vals.sorCurr.textContent = fmtN(user.sortino);
    ui.vals.sorOpt.textContent = fmtN(opt.sortino);
    setBadge('val-sor-delta', user.sortino, opt.sortino, true, false);

    ui.vals.cvarCurr.textContent = fmtP(user.cvar);
    ui.vals.cvarOpt.textContent = fmtP(opt.cvar);
    setBadge('val-cvar-delta', user.cvar, opt.cvar, false, true);

    ui.vals.ddCurr.textContent = fmtP(user.stress_drawdown);
    ui.vals.ddOpt.textContent = fmtP(opt.stress_drawdown);
    setBadge('val-dd-delta', user.stress_drawdown, opt.stress_drawdown, false, true);

    updateChart(data.summary_data, user, opt);
    renderStockTable(data.tickers, user.weights, opt.weights);
    renderStockComparisonPies(data.tickers, user.weights, opt.weights);
    renderSectorComparisonPies(data.sector_data);
    renderSectorCards(data.sector_data);
    if (data.volatility_contribution) renderVolatilityContribution(data.volatility_contribution);
    if (data.rolling_volatility) renderRollingVolatility(data.rolling_volatility);
}

function renderStockTable(tickers, userW, optW) {
    ui.stockTableBody.innerHTML = tickers.map((t, i) => {
        const u = (userW[i] * 100).toFixed(1);
        const o = (optW[i] * 100).toFixed(1);
        const isHigher = optW[i] > userW[i];
        return `
        <tr class="border-b border-white/5 hover:bg-white/5 transition-colors group">
            <td class="py-2 text-white font-bold group-hover:text-primary transition-colors text-[10px]">${t}</td>
            <td class="py-2 text-right text-slate-400 font-mono text-[10px]">${u}%</td>
            <td class="py-2 text-right font-mono font-bold text-[10px] ${isHigher ? 'text-accent' : 'text-slate-500'}">${o}%</td>
        </tr>`;
    }).join('');
}

function renderStockComparisonPies(tickers, userW, optW) {
    const commonOpts = {
        type: 'doughnut',
        options: {
            cutout: '70%',
            plugins: { legend: { display: true, position: 'right', labels: { color: '#8E9AAF', font: { size: 9, family: 'Roboto Mono' }, boxWidth: 10 } }, tooltip: { enabled: true } },
            maintainAspectRatio: false,
            borderWidth: 0
        }
    };

    // User Pie
    if (appState.stockPieUser) appState.stockPieUser.destroy();
    appState.stockPieUser = new Chart(document.getElementById('pieStockUser'), {
        ...commonOpts,
        data: {
            labels: tickers,
            datasets: [{ data: userW, backgroundColor: ['#3A86FF', '#06D6A0', '#EF476F', '#FFBE0B', '#8338EC', '#FB5607'], borderWidth: 0 }]
        }
    });

    // Opt Pie
    if (appState.stockPieOpt) appState.stockPieOpt.destroy();
    appState.stockPieOpt = new Chart(document.getElementById('pieStockOpt'), {
        ...commonOpts,
        data: {
            labels: tickers,
            datasets: [{ data: optW, backgroundColor: ['#3A86FF', '#06D6A0', '#EF476F', '#FFBE0B', '#8338EC', '#FB5607'], borderWidth: 0 }]
        }
    });
}

function renderVolatilityContribution(volData) {
    const canvas = document.getElementById('volatilityChart');
    if (appState.volChart) appState.volChart.destroy();

    // Debug log to verify incoming data
    console.log("Volatility Contribution Data:", volData);

    appState.volChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: volData.labels,
            datasets: [{
                label: 'Risk Contribution %',
                data: volData.values,
                backgroundColor: '#60a5fa',
                borderRadius: 4,
                borderSkipped: false,
                barThickness: 28
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { right: 40, left: 10 } },
            scales: {
                x: {
                    grid: { color: '#2A2E35' },
                    ticks: {
                        color: '#8E9AAF',
                        font: { family: 'Roboto Mono', size: 10 },
                        callback: v => v.toFixed(0) + '%'
                    },
                    min: 0,
                    max: 50
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        color: '#8E9AAF',
                        font: { family: 'Roboto Mono', size: 11, weight: 'bold' }
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `Risk: ${ctx.raw.toFixed(2)}%`
                    }
                }
            }
        }
    });
}

function renderRollingVolatility(rollingData) {
    const canvas = document.getElementById('rollingVolatilityChart');
    if (!canvas) return;

    // Destroy existing chart if any
    if (appState.rollingVolChart) appState.rollingVolChart.destroy();

    appState.rollingVolChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: rollingData.dates,
            datasets: [
                {
                    label: 'User Portfolio',
                    data: rollingData.user,
                    borderColor: '#60A5FA',
                    backgroundColor: 'rgba(96, 165, 250, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: 'Optimal Portfolio',
                    data: rollingData.optimal,
                    borderColor: '#34D399',
                    backgroundColor: 'rgba(52, 211, 153, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: {
                        color: '#8E9AAF',
                        font: { family: 'Roboto Mono', size: 9 },
                        maxRotation: 45,
                        maxTicksLimit: 8
                    }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: {
                        color: '#8E9AAF',
                        font: { family: 'Roboto Mono', size: 10 },
                        callback: (val) => val.toFixed(0) + '%'
                    },
                    title: {
                        display: true,
                        text: 'Annualized Volatility (%)',
                        color: '#8E9AAF',
                        font: { size: 10 }
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1A1D23',
                    titleColor: '#fff',
                    bodyColor: '#CBD5E1',
                    borderColor: '#3B82F6',
                    borderWidth: 1,
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.toFixed(2)}%`
                    }
                }
            }
        }
    });
}


function renderSectorComparisonPies(sectorData) {
    const user = sectorData.user;
    const opt = sectorData.optimal;
    const labels = Object.keys(user);
    const uVals = Object.values(user);
    const oVals = labels.map(k => opt[k] || 0);

    const commonOpts = {
        type: 'doughnut',
        options: { cutout: '65%', plugins: { legend: { display: true, position: 'right', labels: { color: '#8E9AAF', font: { size: 9, family: 'Roboto Mono' }, boxWidth: 10 } } }, maintainAspectRatio: false, borderWidth: 0 }
    };

    if (appState.sectorPieUser) appState.sectorPieUser.destroy();
    appState.sectorPieUser = new Chart(document.getElementById('pieSectorUser'), {
        ...commonOpts, data: { labels, datasets: [{ data: uVals, backgroundColor: ['#3A86FF', '#8338EC', '#FF006E', '#FB5607', '#FFBE0B', '#06D6A0'], borderWidth: 0 }] }
    });

    if (appState.sectorPieOpt) appState.sectorPieOpt.destroy();
    appState.sectorPieOpt = new Chart(document.getElementById('pieSectorOpt'), {
        ...commonOpts, data: { labels, datasets: [{ data: oVals, backgroundColor: ['#3A86FF', '#8338EC', '#FF006E', '#FB5607', '#FFBE0B', '#06D6A0'], borderWidth: 0 }] }
    });
}

function renderSectorCards(sectorData) {
    const userSectors = sectorData.user;
    const optSectors = sectorData.optimal;
    const allSectors = new Set([...Object.keys(userSectors), ...Object.keys(optSectors)]);
    const icons = { 'Technology': 'memory', 'Healthcare': 'health_and_safety', 'Financials': 'account_balance', 'Energy': 'bolt', 'Consumer Staples': 'shopping_basket', 'Utilities': 'water_drop', 'Real Estate': 'apartment', 'Communication': 'cell_tower', 'Industrials': 'factory', 'Materials': 'diamond' };

    // Limit to 6 sectors for 3x2 grid
    const sectorsArray = Array.from(allSectors).slice(0, 6);

    ui.gauges.innerHTML = sectorsArray.map(sector => {
        const uVal = (userSectors[sector] || 0);
        const oVal = (optSectors[sector] || 0);
        const diff = oVal - uVal;
        const isIncrease = diff > 0.001;
        const isDecrease = diff < -0.001;
        const maxVal = Math.max(uVal, oVal, 0.01) * 100; // Scale for bar width

        const statusColor = isIncrease ? 'text-accent' : (isDecrease ? 'text-red-400' : 'text-slate-500');
        const bgColor = isIncrease ? 'bg-accent/5 border-accent/20' : (isDecrease ? 'bg-red-400/5 border-red-400/20' : 'bg-slate-800/10 border-slate-700/50');

        return `
        <div class="${bgColor} border p-4 rounded-xl flex flex-col gap-3 shadow-lg transition-all hover:scale-[1.02] hover:shadow-xl group">
            <!-- HEADER -->
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <div class="size-8 rounded-lg bg-gunmetal flex items-center justify-center border border-slate-700 group-hover:border-primary transition-colors">
                        <span class="material-symbols-outlined text-lg ${statusColor}">${icons[sector] || 'category'}</span>
                    </div>
                    <span class="text-[10px] font-bold uppercase tracking-widest text-slate-400">${sector}</span>
                </div>
                <div class="flex items-center gap-1 ${statusColor} font-mono text-[10px] font-bold">
                    ${isIncrease ? '▲' : (isDecrease ? '▼' : '•')} ${(Math.abs(diff) * 100).toFixed(1)}%
                </div>
            </div>
            
            <!-- BAR GRAPH -->
            <div class="flex flex-col gap-2">
                <!-- Current Bar (Light Blue) -->
                <div class="flex items-center gap-2">
                    <span class="text-[9px] font-bold text-blue-300 w-10">Curr</span>
                    <div class="flex-1 h-3 bg-black/20 rounded-full overflow-hidden">
                        <div class="h-full rounded-full" style="background-color: #60a5fa; width: ${(uVal / (maxVal / 100)) * 100}%"></div>
                    </div>
                    <span class="text-[10px] font-mono text-blue-300 w-10 text-right">${(uVal * 100).toFixed(1)}%</span>
                </div>
                <!-- Optimal Bar (Dark Blue) -->
                <div class="flex items-center gap-2">
                    <span class="text-[9px] font-bold text-blue-600 w-10">Opt</span>
                    <div class="flex-1 h-3 bg-black/20 rounded-full overflow-hidden">
                        <div class="h-full rounded-full shadow-[0_0_8px_rgba(29,78,216,0.5)]" style="background-color: #1d4ed8; width: ${(oVal / (maxVal / 100)) * 100}%"></div>
                    </div>
                    <span class="text-[10px] font-mono text-white w-10 text-right">${(oVal * 100).toFixed(1)}%</span>
                </div>
            </div>

        </div>`;
    }).join('');
}

// Pie charts removed in favor of integrated stock/sector visualizations

function initChart() {
    const ctx = document.getElementById('frontierChart').getContext('2d');
    Chart.defaults.color = '#8E9AAF';
    Chart.defaults.font.family = 'Roboto Mono';
    appState.chartInstance = new Chart(ctx, {
        type: 'scatter',
        data: { datasets: [{ label: 'Simulation', data: [], backgroundColor: '#2A2E35', pointRadius: 1 }, { label: 'Current', data: [], backgroundColor: '#EF476F', pointRadius: 6 }, { label: 'Optimal', data: [], backgroundColor: '#3A86FF', pointRadius: 8 }] },
        options: { responsive: true, maintainAspectRatio: false, scales: { x: { title: { display: true, text: 'Volatility (Risk)' }, grid: { color: '#2A2E35' } }, y: { title: { display: true, text: 'Return' }, grid: { color: '#2A2E35' } } }, plugins: { legend: { display: false } } }
    });
}

function updateChart(summary, user, opt) {
    appState.chartInstance.data.datasets[0].data = summary.returns.map((r, i) => ({ x: summary.volatility[i], y: r }));
    appState.chartInstance.data.datasets[1].data = [{ x: user.volatility, y: user.return }];
    appState.chartInstance.data.datasets[2].data = [{ x: opt.volatility, y: opt.return }];
    appState.chartInstance.update();
}
