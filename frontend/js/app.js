/**
 * StockPulse — Main Dashboard App v2
 * Orchestrates tabs, market overview, screener, heatmap, and stock detail.
 */
(function () {
    'use strict';

    let companies = [];
    let currentSymbol = null;
    let currentDays = 90;

    const $ = id => document.getElementById(id);

    // ═══════════════════════════════════════════════════════════════
    //  INITIALIZATION
    // ═══════════════════════════════════════════════════════════════
    async function init() {
        try {
            companies = await Api.getCompanies();
            renderCompanyList(companies);
            populateCompareDropdowns(companies);
            loadGainersLosers();
            loadMarketOverview();
            bindEvents();
            $('market-status').textContent = `● ${companies.length} stocks loaded`;
        } catch (err) {
            console.error('Init failed:', err);
            $('market-status').textContent = '● Connection Error';
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  TAB NAVIGATION
    // ═══════════════════════════════════════════════════════════════
    function switchTab(tabName) {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tabName));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        const pane = $(`pane-${tabName}`);
        if (pane) pane.classList.add('active');

        // Lazy-load heatmap
        if (tabName === 'heatmap') loadHeatmap();
    }

    // ═══════════════════════════════════════════════════════════════
    //  SIDEBAR
    // ═══════════════════════════════════════════════════════════════
    function renderCompanyList(list) {
        $('company-list').innerHTML = list.map(c => `
            <li class="company-item" data-symbol="${c.symbol}" id="company-${c.symbol.replace('.', '-')}">
                <span class="company-item__name">${c.name}</span>
                <span class="company-item__symbol">${Utils.cleanSymbol(c.symbol)}</span>
            </li>
        `).join('');
    }

    function setActiveCompany(symbol) {
        document.querySelectorAll('.company-item').forEach(el => el.classList.toggle('active', el.dataset.symbol === symbol));
    }

    async function loadGainersLosers() {
        try {
            const data = await Api.getGainersLosers(5);
            $('gainers-list').innerHTML = (data.gainers || []).map(g => `
                <li class="mover-item"><span class="mover-item__symbol">${Utils.cleanSymbol(g.symbol)}</span>
                <span class="mover-item__return">+${Math.abs(g.daily_return).toFixed(2)}%</span></li>
            `).join('') || '<li class="mover-item"><span class="mover-item__symbol">No data</span></li>';
            $('losers-list').innerHTML = (data.losers || []).map(l => `
                <li class="mover-item"><span class="mover-item__symbol">${Utils.cleanSymbol(l.symbol)}</span>
                <span class="mover-item__return">${l.daily_return.toFixed(2)}%</span></li>
            `).join('') || '<li class="mover-item"><span class="mover-item__symbol">No data</span></li>';
        } catch (err) { console.error('Gainers/losers failed:', err); }
    }

    // ═══════════════════════════════════════════════════════════════
    //  MARKET OVERVIEW
    // ═══════════════════════════════════════════════════════════════
    async function loadMarketOverview() {
        try {
            const [overview, screenAll] = await Promise.all([
                Api.getMarketOverview(),
                Api.getScreener(),
            ]);

            $('overview-date').textContent = overview.date ? `As of ${Utils.formatDate(overview.date)}` : '';
            $('pulse-breadth').textContent = `${overview.market_breadth}%`;
            $('breadth-bar').style.width = `${overview.market_breadth}%`;
            $('pulse-advances').textContent = overview.advances;
            $('pulse-declines').textContent = overview.declines;

            const sentEl = $('pulse-sentiment');
            const sentInfo = Utils.sentimentLabel(overview.avg_sentiment);
            sentEl.textContent = sentInfo.label;
            sentEl.style.color = sentInfo.color;

            // Sector cards
            const sectorGrid = $('sector-grid');
            sectorGrid.innerHTML = overview.sectors.map((s, i) => {
                const color = s.avg_return >= 0 ? 'var(--gain)' : 'var(--loss)';
                const prefix = s.avg_return >= 0 ? '+' : '';
                const barWidth = Math.min(Math.abs(s.avg_return) * 10, 100);
                return `<div class="sector-card" style="animation-delay:${i * 0.05}s">
                    <div class="sector-card__name">${s.sector}</div>
                    <div class="sector-card__return" style="color:${color}">${prefix}${s.avg_return}%</div>
                    <div class="sector-card__count">${s.count} stock${s.count > 1 ? 's' : ''}</div>
                    <div class="sector-card__bar"><div class="sector-card__bar-fill" style="width:${barWidth}%;background:${color}"></div></div>
                </div>`;
            }).join('');

            // Stock mini-cards
            const cardsGrid = $('stock-cards-grid');
            cardsGrid.innerHTML = screenAll.map((s, i) => {
                const retColor = s.daily_return >= 0 ? 'var(--gain)' : 'var(--loss)';
                const retBg = s.daily_return >= 0 ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)';
                const prefix = s.daily_return >= 0 ? '+' : '';
                return `<div class="stock-mini-card" data-symbol="${s.symbol}" style="animation-delay:${i * 0.03}s">
                    <div class="stock-mini-card__header">
                        <span class="stock-mini-card__symbol">${Utils.cleanSymbol(s.symbol)}</span>
                        <span class="stock-mini-card__return" style="color:${retColor};background:${retBg}">${prefix}${s.daily_return}%</span>
                    </div>
                    <div class="stock-mini-card__name">${s.name}</div>
                    <div class="stock-mini-card__price">${Utils.formatCurrency(s.close)}</div>
                    <div class="stock-mini-card__meta">
                        <span>Vol: ${s.volatility}%</span>
                        <span>Sent: ${s.sentiment_score}</span>
                        <span>${s.sector}</span>
                    </div>
                </div>`;
            }).join('');
        } catch (err) { console.error('Market overview failed:', err); }
    }

    // ═══════════════════════════════════════════════════════════════
    //  STOCK DETAIL
    // ═══════════════════════════════════════════════════════════════
    async function loadStock(symbol, days) {
        currentSymbol = symbol;
        currentDays = days || currentDays;
        setActiveCompany(symbol);
        switchTab('stock');

        $('welcome-screen').style.display = 'none';
        $('stock-detail').style.display = 'block';
        $('chart-loading').classList.remove('hidden');

        try {
            const [stockData, summary] = await Promise.all([
                Api.getStockData(symbol, currentDays),
                Api.getSummary(symbol),
            ]);

            $('stock-name').textContent = summary.name;
            $('stock-symbol').textContent = Utils.cleanSymbol(summary.symbol);
            $('stock-sector').textContent = summary.sector;
            $('stock-price').textContent = Utils.formatCurrency(summary.latest_close);

            const changeEl = $('stock-change');
            if (summary.latest_daily_return != null) {
                const pct = Utils.formatPercent(summary.latest_daily_return);
                changeEl.textContent = pct.text;
                changeEl.className = 'stock-header__change ' + pct.className;
            } else { changeEl.textContent = '—'; changeEl.className = 'stock-header__change'; }

            Utils.animateValue($('stat-high52'), summary.high_52w, 600, v => Utils.formatCurrency(v));
            Utils.animateValue($('stat-low52'), summary.low_52w, 600, v => Utils.formatCurrency(v));
            Utils.animateValue($('stat-avg'), summary.avg_close, 600, v => Utils.formatCurrency(v));

            const volEl = $('stat-volatility');
            const volInfo = Utils.volatilityLabel(summary.latest_volatility);
            volEl.textContent = volInfo.label; volEl.style.color = volInfo.color;

            const sentEl = $('stat-sentiment');
            const sentInfo = Utils.sentimentLabel(summary.latest_sentiment);
            sentEl.textContent = sentInfo.label; sentEl.style.color = sentInfo.color;

            const retEl = $('stat-return');
            if (summary.latest_daily_return != null) {
                const p = Utils.formatPercent(summary.latest_daily_return);
                retEl.textContent = p.text;
                retEl.style.color = p.className === 'positive' ? '#10b981' : '#ef4444';
            } else { retEl.textContent = '—'; retEl.style.color = ''; }

            // RSI
            const rsiEl = $('stat-rsi');
            const rsiBar = $('rsi-bar');
            if (summary.rsi != null) {
                rsiEl.textContent = summary.rsi.toFixed(1);
                rsiBar.style.width = `${summary.rsi}%`;
                if (summary.rsi >= 70) { rsiEl.style.color = '#ef4444'; rsiBar.style.background = '#ef4444'; }
                else if (summary.rsi <= 30) { rsiEl.style.color = '#10b981'; rsiBar.style.background = '#10b981'; }
                else { rsiEl.style.color = '#f59e0b'; rsiBar.style.background = '#f59e0b'; }
            } else { rsiEl.textContent = '—'; rsiBar.style.width = '0'; }

            // Export button
            $('export-btn').onclick = () => {
                window.open(Api.getExportUrl(symbol, currentDays), '_blank');
            };

            // Chart
            $('chart-loading').classList.add('hidden');
            ChartManager.createMainChart('chart-container', 'volume-chart-container');
            ChartManager.updateMainChart(stockData);

            $('prediction-results').style.display = 'none';
            $('predict-btn').style.display = 'inline-flex';
            $('predict-btn').textContent = 'Generate 7-Day Forecast';
            $('predict-btn').disabled = false;

        } catch (err) {
            console.error('Failed to load stock:', err);
            $('chart-loading').innerHTML = `<span style="color:#ef4444">Failed to load data</span>`;
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  PREDICTION
    // ═══════════════════════════════════════════════════════════════
    async function loadPrediction() {
        if (!currentSymbol) return;
        const btn = $('predict-btn');
        btn.textContent = 'Predicting...'; btn.disabled = true;

        try {
            const result = await Api.getPrediction(currentSymbol, 7);
            $('prediction-results').style.display = 'block';
            btn.style.display = 'none';

            $('prediction-r2').textContent = result.r2_score != null
                ? `Model R\u00B2 Score: ${result.r2_score.toFixed(4)} (1.0 = perfect)` : 'R\u00B2 Score: N/A';

            $('prediction-tbody').innerHTML = result.predictions.map(p => `
                <tr><td>${Utils.formatDate(p.date)}</td><td>${Utils.formatCurrency(p.predicted_close)}</td></tr>
            `).join('');

            ChartManager.addPredictionLine(result.predictions);
        } catch (err) {
            console.error('Prediction failed:', err);
            btn.textContent = 'Retry Prediction'; btn.disabled = false;
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  COMPARE
    // ═══════════════════════════════════════════════════════════════
    function populateCompareDropdowns(companies) {
        const opts = companies.map(c => `<option value="${c.symbol}">${Utils.cleanSymbol(c.symbol)} - ${c.name}</option>`).join('');
        $('compare-stock1').innerHTML = opts;
        $('compare-stock2').innerHTML = opts;
        if (companies.length >= 2) $('compare-stock2').selectedIndex = 1;
    }

    async function loadComparison() {
        const sym1 = $('compare-stock1').value;
        const sym2 = $('compare-stock2').value;
        if (sym1 === sym2) { alert('Select two different stocks.'); return; }

        const btn = $('compare-btn');
        btn.textContent = 'Comparing...'; btn.disabled = true;

        try {
            const r = await Api.compareStocks(sym1, sym2, 90);
            $('compare-results').style.display = 'block';

            $('compare-metrics').innerHTML = `
                <div class="compare-metric"><div class="compare-metric__label">Correlation</div>
                <div class="compare-metric__value" style="color:${r.correlation > 0.7 ? '#10b981' : r.correlation > 0.3 ? '#f59e0b' : '#ef4444'}">${r.correlation != null ? r.correlation.toFixed(4) : '—'}</div></div>
                <div class="compare-metric"><div class="compare-metric__label">${Utils.cleanSymbol(sym1)} Return</div>
                <div class="compare-metric__value" style="color:${(r.cumulative_return1||0) >= 0 ? '#10b981' : '#ef4444'}">${r.cumulative_return1 != null ? r.cumulative_return1.toFixed(2) + '%' : '—'}</div></div>
                <div class="compare-metric"><div class="compare-metric__label">${Utils.cleanSymbol(sym2)} Return</div>
                <div class="compare-metric__value" style="color:${(r.cumulative_return2||0) >= 0 ? '#10b981' : '#ef4444'}">${r.cumulative_return2 != null ? r.cumulative_return2.toFixed(2) + '%' : '—'}</div></div>
                <div class="compare-metric"><div class="compare-metric__label">${Utils.cleanSymbol(sym1)} Vol</div>
                <div class="compare-metric__value">${r.volatility1 != null ? r.volatility1.toFixed(1) + '%' : '—'}</div></div>
                <div class="compare-metric"><div class="compare-metric__label">${Utils.cleanSymbol(sym2)} Vol</div>
                <div class="compare-metric__value">${r.volatility2 != null ? r.volatility2.toFixed(1) + '%' : '—'}</div></div>`;

            ChartManager.createCompareChart('compare-chart-container', r.data1, r.data2, Utils.cleanSymbol(sym1), Utils.cleanSymbol(sym2));
        } catch (err) { console.error('Compare failed:', err); }
        finally { btn.textContent = 'Compare'; btn.disabled = false; }
    }

    // ═══════════════════════════════════════════════════════════════
    //  SCREENER
    // ═══════════════════════════════════════════════════════════════
    async function runScreener() {
        const params = {};
        const minRet = $('filter-min-return').value;
        const maxVol = $('filter-max-vol').value;
        const minSent = $('filter-min-sent').value;
        const sector = $('filter-sector').value;
        if (minRet) params.min_return = parseFloat(minRet);
        if (maxVol) params.max_volatility = parseFloat(maxVol);
        if (minSent) params.min_sentiment = parseFloat(minSent);
        if (sector) params.sector = sector;

        try {
            const results = await Api.getScreener(params);
            renderScreenerResults(results);
        } catch (err) { console.error('Screener failed:', err); }
    }

    async function resetScreener() {
        $('filter-min-return').value = '';
        $('filter-max-vol').value = '';
        $('filter-min-sent').value = '';
        $('filter-sector').value = '';
        try {
            const results = await Api.getScreener();
            renderScreenerResults(results);
        } catch (err) { console.error('Screener failed:', err); }
    }

    function renderScreenerResults(results) {
        if (!results.length) {
            $('screener-results').innerHTML = '<p class="screener-empty">No stocks match the selected filters.</p>';
            return;
        }
        $('screener-results').innerHTML = `<div class="screener-table-wrap"><table class="screener-table">
            <thead><tr><th>Symbol</th><th>Name</th><th>Sector</th><th>Close</th><th>Return</th><th>Volatility</th><th>Sentiment</th><th>7d MA</th></tr></thead>
            <tbody>${results.map(s => {
                const retColor = s.daily_return >= 0 ? 'var(--gain)' : 'var(--loss)';
                return `<tr data-symbol="${s.symbol}">
                    <td style="font-weight:700;color:var(--accent-purple)">${Utils.cleanSymbol(s.symbol)}</td>
                    <td>${s.name}</td><td>${s.sector}</td>
                    <td style="font-weight:700">${Utils.formatCurrency(s.close)}</td>
                    <td style="color:${retColor};font-weight:700">${s.daily_return >= 0 ? '+' : ''}${s.daily_return}%</td>
                    <td>${s.volatility}%</td>
                    <td>${s.sentiment_score}</td>
                    <td>${s.ma_7 ? Utils.formatCurrency(s.ma_7) : '—'}</td>
                </tr>`;
            }).join('')}</tbody></table></div>`;

        // Click row to go to stock detail
        $('screener-results').querySelectorAll('tr[data-symbol]').forEach(row => {
            row.addEventListener('click', () => loadStock(row.dataset.symbol, currentDays));
        });
    }

    // ═══════════════════════════════════════════════════════════════
    //  CORRELATION HEATMAP (Canvas)
    // ═══════════════════════════════════════════════════════════════
    let heatmapLoaded = false;
    async function loadHeatmap() {
        if (heatmapLoaded) return;
        try {
            const data = await Api.getCorrelationMatrix(90);
            drawHeatmap(data.symbols, data.matrix);
            heatmapLoaded = true;
        } catch (err) { console.error('Heatmap failed:', err); }
    }

    function drawHeatmap(symbols, matrix) {
        const canvas = $('heatmap-canvas');
        const ctx = canvas.getContext('2d');
        const n = symbols.length;
        const cellSize = 56;
        const labelOffset = 90;
        const totalSize = labelOffset + n * cellSize;

        canvas.width = totalSize * 2;  // 2x for retina
        canvas.height = totalSize * 2;
        canvas.style.width = totalSize + 'px';
        canvas.style.height = totalSize + 'px';
        ctx.scale(2, 2);

        ctx.fillStyle = '#131838';
        ctx.fillRect(0, 0, totalSize, totalSize);

        // Draw cells
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                const val = matrix[i][j];
                const x = labelOffset + j * cellSize;
                const y = labelOffset + i * cellSize;

                ctx.fillStyle = val != null ? correlationColor(val) : '#1a2048';
                ctx.beginPath();
                roundRect(ctx, x + 2, y + 2, cellSize - 4, cellSize - 4, 6);
                ctx.fill();

                // Value text
                if (val != null) {
                    ctx.fillStyle = Math.abs(val) > 0.5 ? '#ffffff' : '#c4c4e0';
                    ctx.font = '600 11px Inter, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(val.toFixed(2), x + cellSize / 2, y + cellSize / 2);
                }
            }
        }

        // Row labels
        ctx.fillStyle = '#e8eaf6';
        ctx.font = '600 11px Inter, sans-serif';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        for (let i = 0; i < n; i++) {
            ctx.fillText(Utils.cleanSymbol(symbols[i]), labelOffset - 8, labelOffset + i * cellSize + cellSize / 2);
        }

        // Column labels (rotated)
        ctx.textAlign = 'left';
        for (let j = 0; j < n; j++) {
            ctx.save();
            ctx.translate(labelOffset + j * cellSize + cellSize / 2, labelOffset - 8);
            ctx.rotate(-Math.PI / 4);
            ctx.fillText(Utils.cleanSymbol(symbols[j]), 0, 0);
            ctx.restore();
        }
    }

    function correlationColor(val) {
        if (val == null) return '#1a2048';
        // Red(-1) -> Yellow(0) -> Green(+1)
        const t = (val + 1) / 2; // 0 to 1
        const r = Math.round(239 - t * 200);
        const g = Math.round(68 + t * 117);
        const b = Math.round(68 + t * 60);
        return `rgba(${r}, ${g}, ${b}, 0.85)`;
    }

    function roundRect(ctx, x, y, w, h, r) {
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + w - r, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + r);
        ctx.lineTo(x + w, y + h - r);
        ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        ctx.lineTo(x + r, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - r);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
    }

    // ═══════════════════════════════════════════════════════════════
    //  EVENTS
    // ═══════════════════════════════════════════════════════════════
    function bindEvents() {
        // Tab clicks
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => switchTab(tab.dataset.tab));
        });

        // Company click
        $('company-list').addEventListener('click', e => {
            const item = e.target.closest('.company-item');
            if (item) loadStock(item.dataset.symbol, currentDays);
        });

        // Stock mini-card click
        $('stock-cards-grid').addEventListener('click', e => {
            const card = e.target.closest('.stock-mini-card');
            if (card) loadStock(card.dataset.symbol, currentDays);
        });

        // Time filter
        document.querySelectorAll('.time-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                if (currentSymbol) loadStock(currentSymbol, parseInt(btn.dataset.days));
            });
        });

        // Search
        $('search-input').addEventListener('input', e => {
            const q = e.target.value.toLowerCase();
            const filtered = companies.filter(c => c.name.toLowerCase().includes(q) || c.symbol.toLowerCase().includes(q));
            renderCompanyList(filtered);
        });
    }

    // ─── Public API ───
    window.dashboardApp = {
        loadPrediction,
        loadComparison,
        runScreener,
        resetScreener,
    };

    document.addEventListener('DOMContentLoaded', init);
})();
