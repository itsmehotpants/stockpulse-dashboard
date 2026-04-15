/**
 * StockPulse — Utility Functions
 * Currency formatting, percentage helpers, date utils, counter animation.
 */

const Utils = {
    /**
     * Format a number as Indian Rupees (₹).
     */
    formatCurrency(value) {
        if (value == null || isNaN(value)) return '—';
        return '₹' + Number(value).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    },

    /**
     * Format a percentage value with +/- prefix and color class.
     * Returns { text: '+1.23%', className: 'positive' | 'negative' }
     */
    formatPercent(value) {
        if (value == null || isNaN(value)) return { text: '—', className: '' };
        const pct = (value * 100).toFixed(2);
        const prefix = pct >= 0 ? '+' : '';
        return {
            text: `${prefix}${pct}%`,
            className: pct >= 0 ? 'positive' : 'negative',
        };
    },

    /**
     * Format a date string or Date object to a readable form.
     */
    formatDate(d) {
        if (!d) return '—';
        const dt = typeof d === 'string' ? new Date(d) : d;
        return dt.toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
        });
    },

    /**
     * Clean symbol for display: remove .NS / .BO suffix.
     */
    cleanSymbol(symbol) {
        return symbol.replace(/\.(NS|BO)$/i, '');
    },

    /**
     * Animated counter: ticks from 0 to `target` over `duration` ms.
     */
    animateValue(element, target, duration = 800, formatter = null) {
        if (target == null || isNaN(target)) {
            element.textContent = '—';
            return;
        }

        const start = 0;
        const startTime = performance.now();

        function tick(now) {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease-out quad
            const eased = 1 - (1 - progress) * (1 - progress);
            const current = start + (target - start) * eased;

            if (formatter) {
                element.textContent = formatter(current);
            } else {
                element.textContent = current.toFixed(2);
            }

            if (progress < 1) {
                requestAnimationFrame(tick);
            }
        }
        requestAnimationFrame(tick);
    },

    /**
     * Get a sentiment label and color.
     */
    sentimentLabel(score) {
        if (score == null) return { label: '—', color: '#8f93b0' };
        if (score >= 70) return { label: `${score.toFixed(0)} Bullish`, color: '#10b981' };
        if (score >= 40) return { label: `${score.toFixed(0)} Neutral`, color: '#f59e0b' };
        return { label: `${score.toFixed(0)} Bearish`, color: '#ef4444' };
    },

    /**
     * Get a volatility label and color.
     */
    volatilityLabel(vol) {
        if (vol == null) return { label: '—', color: '#8f93b0' };
        const pct = (vol * 100).toFixed(1);
        if (vol < 0.15) return { label: `${pct}% Low`, color: '#10b981' };
        if (vol < 0.30) return { label: `${pct}% Med`, color: '#f59e0b' };
        return { label: `${pct}% High`, color: '#ef4444' };
    },
};
