/**
 * StockPulse — API Client v2
 * Centralized fetch wrapper with caching for all backend endpoints.
 */

const API_BASE = '/api/v1';

// Simple in-memory cache with TTL
const _cache = {};
const CACHE_TTL = 60000; // 1 minute

const Api = {
    async _fetch(url, useCache = false) {
        if (useCache && _cache[url] && Date.now() - _cache[url].ts < CACHE_TTL) {
            return _cache[url].data;
        }
        try {
            const response = await fetch(url);
            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || `HTTP ${response.status}`);
            }
            const data = await response.json();
            if (useCache) _cache[url] = { data, ts: Date.now() };
            return data;
        } catch (error) {
            console.error(`API Error [${url}]:`, error.message);
            throw error;
        }
    },

    async getCompanies() { return this._fetch(`${API_BASE}/companies`, true); },

    async getStockData(symbol, days = 90) {
        return this._fetch(`${API_BASE}/data/${encodeURIComponent(symbol)}?days=${days}`);
    },

    async getSummary(symbol) {
        return this._fetch(`${API_BASE}/summary/${encodeURIComponent(symbol)}`);
    },

    async compareStocks(symbol1, symbol2, days = 90) {
        return this._fetch(
            `${API_BASE}/compare?symbol1=${encodeURIComponent(symbol1)}&symbol2=${encodeURIComponent(symbol2)}&days=${days}`
        );
    },

    async getPrediction(symbol, days = 7) {
        return this._fetch(`${API_BASE}/predict/${encodeURIComponent(symbol)}?days=${days}`);
    },

    async getGainersLosers(n = 5) {
        return this._fetch(`${API_BASE}/gainers-losers?n=${n}`, true);
    },

    async getMarketOverview() {
        return this._fetch(`${API_BASE}/market-overview`, true);
    },

    async getCorrelationMatrix(days = 90) {
        return this._fetch(`${API_BASE}/correlation?days=${days}`, true);
    },

    async getScreener(params = {}) {
        const qs = new URLSearchParams();
        if (params.min_return != null) qs.append('min_return', params.min_return);
        if (params.max_volatility != null) qs.append('max_volatility', params.max_volatility);
        if (params.min_sentiment != null) qs.append('min_sentiment', params.min_sentiment);
        if (params.sector) qs.append('sector', params.sector);
        return this._fetch(`${API_BASE}/screener?${qs.toString()}`);
    },

    getExportUrl(symbol, days = 365) {
        return `${API_BASE}/export/${encodeURIComponent(symbol)}?days=${days}`;
    },
};
