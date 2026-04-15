/**
 * StockPulse — Chart Manager v2
 * TradingView Lightweight Charts with candlestick, MA, volume, and prediction.
 */

const ChartManager = {
    chart: null,
    candleSeries: null,
    maSeries: null,
    volumeSeries: null,
    predictionSeries: null,
    volumeChart: null,
    compareChart: null,

    chartOptions: {
        layout: {
            background: { type: 'solid', color: '#131838' },
            textColor: '#8f93b0',
            fontSize: 11,
            fontFamily: "'Inter', sans-serif",
        },
        grid: {
            vertLines: { color: 'rgba(255,255,255,0.03)' },
            horzLines: { color: 'rgba(255,255,255,0.03)' },
        },
        crosshair: {
            mode: 0,
            vertLine: { color: '#7c3aed', width: 1, style: 2, labelBackgroundColor: '#7c3aed' },
            horzLine: { color: '#7c3aed', width: 1, style: 2, labelBackgroundColor: '#7c3aed' },
        },
        timeScale: { borderColor: 'rgba(255,255,255,0.06)', timeVisible: false },
        rightPriceScale: { borderColor: 'rgba(255,255,255,0.06)' },
        handleScroll: { vertTouchDrag: false },
    },

    createMainChart(containerId, volumeContainerId) {
        const container = document.getElementById(containerId);
        const volumeContainer = document.getElementById(volumeContainerId);
        if (!container) return;

        container.innerHTML = '';
        this.chart = null; this.candleSeries = null; this.maSeries = null;
        this.predictionSeries = null; this.volumeChart = null; this.volumeSeries = null;

        // Main candlestick chart
        this.chart = LightweightCharts.createChart(container, {
            ...this.chartOptions,
            width: container.clientWidth,
            height: 350,
        });

        this.candleSeries = this.chart.addCandlestickSeries({
            upColor: '#10b981', downColor: '#ef4444',
            borderDownColor: '#ef4444', borderUpColor: '#10b981',
            wickDownColor: '#ef4444', wickUpColor: '#10b981',
        });

        this.maSeries = this.chart.addLineSeries({
            color: '#7c3aed', lineWidth: 2, lineStyle: 0,
            priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
        });

        // Volume chart
        if (volumeContainer) {
            volumeContainer.innerHTML = '';
            this.volumeChart = LightweightCharts.createChart(volumeContainer, {
                ...this.chartOptions,
                width: volumeContainer.clientWidth,
                height: 70,
                rightPriceScale: { borderColor: 'rgba(255,255,255,0.06)', scaleMargins: { top: 0.1, bottom: 0 } },
                timeScale: { visible: false },
            });

            this.volumeSeries = this.volumeChart.addHistogramSeries({
                priceFormat: { type: 'volume' },
                priceScaleId: '',
            });

            // Sync time scales
            this.chart.timeScale().subscribeVisibleLogicalRangeChange(range => {
                if (this.volumeChart && range) {
                    this.volumeChart.timeScale().setVisibleLogicalRange(range);
                }
            });
        }

        // Resize observer
        const ro = new ResizeObserver(entries => {
            const w = entries[0].contentRect.width;
            if (this.chart) this.chart.applyOptions({ width: w });
            if (this.volumeChart) this.volumeChart.applyOptions({ width: w });
        });
        ro.observe(container);
    },

    updateMainChart(data) {
        if (!this.candleSeries || !data.length) return;

        const candleData = data.map(d => ({ time: d.date, open: d.open, high: d.high, low: d.low, close: d.close }));
        this.candleSeries.setData(candleData);

        const maData = data.filter(d => d.ma_7 != null).map(d => ({ time: d.date, value: d.ma_7 }));
        this.maSeries.setData(maData);

        // Volume histogram with green/red coloring
        if (this.volumeSeries) {
            const volData = data.map(d => ({
                time: d.date,
                value: d.volume,
                color: d.close >= d.open ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)',
            }));
            this.volumeSeries.setData(volData);
        }

        this.chart.timeScale().fitContent();
        if (this.volumeChart) this.volumeChart.timeScale().fitContent();
    },

    addPredictionLine(predictions) {
        if (!this.chart || !predictions.length) return;
        if (this.predictionSeries) this.chart.removeSeries(this.predictionSeries);

        this.predictionSeries = this.chart.addLineSeries({
            color: '#f59e0b', lineWidth: 2, lineStyle: 2,
            priceLineVisible: false, lastValueVisible: true, crosshairMarkerVisible: true,
        });
        this.predictionSeries.setData(predictions.map(p => ({ time: p.date, value: p.predicted_close })));
        this.chart.timeScale().fitContent();
    },

    createCompareChart(containerId, data1, data2, label1, label2) {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = '';

        this.compareChart = LightweightCharts.createChart(container, {
            ...this.chartOptions, width: container.clientWidth, height: 280,
        });

        const norm1 = this._normalizeToBase100(data1);
        const norm2 = this._normalizeToBase100(data2);

        const s1 = this.compareChart.addLineSeries({ color: '#7c3aed', lineWidth: 2, priceLineVisible: false });
        s1.setData(norm1);
        const s2 = this.compareChart.addLineSeries({ color: '#00d4aa', lineWidth: 2, priceLineVisible: false });
        s2.setData(norm2);

        this.compareChart.timeScale().fitContent();

        const ro = new ResizeObserver(entries => {
            if (this.compareChart) this.compareChart.applyOptions({ width: entries[0].contentRect.width });
        });
        ro.observe(container);
    },

    _normalizeToBase100(data) {
        if (!data.length) return [];
        const base = data[0].close;
        if (!base) return [];
        return data.map(d => ({ time: d.date, value: (d.close / base) * 100 }));
    },
};
