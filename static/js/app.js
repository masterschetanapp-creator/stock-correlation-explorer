// ===================================================================
// STOCK CORRELATION EXPLORER — Multi-Factor Market Nexus
// ===================================================================

// --- GLOBAL STATE ---
const state = {
  data: null,
  mainChart: null,
  overlayChart: null,
  corrChart: null,
  stockSeries: null,
  overlaySeries: {},
  factorMap: {},
  sortedDates: [],
  currentSymbol: '',
  currentPeriod: '5y',
  debounceTimer: null,
  newsDebounceTimer: null,
  lastNewsDate: null,
};

// --- FACTOR CONFIG ---
const FACTORS = {
  usdinr: { label: 'USD/INR', icon: '💱', color: '#9c27b0', unit: '₹', prefix: '₹' },
  gold:   { label: 'Gold',    icon: '🥇', color: '#ffd700', unit: 'USD/oz', prefix: '$' },
  silver: { label: 'Silver',  icon: '🥈', color: '#c0c0c0', unit: 'USD/oz', prefix: '$' },
  oil:    { label: 'Crude Oil', icon: '🛢️', color: '#e67e22', unit: 'USD/bbl', prefix: '$' },
};

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
  initSearch();
  initPeriodButtons();
  initFactorToggles();
  initSimulatorControls();

  // Load default stock on startup
  document.getElementById('stock-input').value = 'RELIANCE.NS';
  analyzeStock();
});


// ===================================================================
// SEARCH & SUGGESTIONS
// ===================================================================

function initSearch() {
  const input = document.getElementById('stock-input');
  const btn = document.getElementById('search-btn');
  const dropdown = document.getElementById('suggestions-dropdown');

  input.addEventListener('input', () => {
    clearTimeout(state.debounceTimer);
    const q = input.value.trim();
    if (q.length < 1) {
      dropdown.classList.add('hidden');
      return;
    }
    state.debounceTimer = setTimeout(() => fetchSuggestions(q), 250);
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      dropdown.classList.add('hidden');
      analyzeStock();
    }
  });

  btn.addEventListener('click', () => {
    dropdown.classList.add('hidden');
    analyzeStock();
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-wrapper')) {
      dropdown.classList.add('hidden');
    }
  });
}

async function fetchSuggestions(query) {
  const dropdown = document.getElementById('suggestions-dropdown');
  try {
    const res = await fetch(`/api/suggest?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error('Suggestion fetch failed');
    const items = await res.json();

    if (!items.length) {
      dropdown.classList.add('hidden');
      return;
    }

    dropdown.innerHTML = items.map(item => `
      <div class="suggestion-item" data-symbol="${escapeHtml(item.symbol)}">
        <span class="suggestion-symbol">${escapeHtml(item.symbol)}</span>
        <span class="suggestion-name">${escapeHtml(item.name)}</span>
      </div>
    `).join('');

    dropdown.querySelectorAll('.suggestion-item').forEach(el => {
      el.addEventListener('click', () => {
        document.getElementById('stock-input').value = el.dataset.symbol;
        dropdown.classList.add('hidden');
        analyzeStock();
      });
    });

    dropdown.classList.remove('hidden');
  } catch (err) {
    console.error('Suggestion error:', err);
    dropdown.classList.add('hidden');
  }
}


// ===================================================================
// PERIOD BUTTONS
// ===================================================================

function initPeriodButtons() {
  document.querySelectorAll('.period-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.currentPeriod = btn.dataset.period;
      if (state.currentSymbol) {
        analyzeStock();
      }
    });
  });
}


// ===================================================================
// FACTOR TOGGLES
// ===================================================================

function initFactorToggles() {
  const toggles = {
    'toggle-usdinr': 'usdinr',
    'toggle-gold': 'gold',
    'toggle-silver': 'silver',
    'toggle-oil': 'oil',
    'toggle-stock': 'stock',
  };

  for (const [id, key] of Object.entries(toggles)) {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('change', (e) => {
        const series = state.overlaySeries[key];
        if (series) {
          series.applyOptions({ visible: e.target.checked });
        }
      });
    }
  }
}


// ===================================================================
// MAIN ANALYZE FUNCTION
// ===================================================================

async function analyzeStock() {
  let symbol = document.getElementById('stock-input').value.trim().toUpperCase();
  if (!symbol) return;

  if (!symbol.endsWith('.NS') && !symbol.endsWith('.BO')) {
    symbol += '.NS';
  }

  state.currentSymbol = symbol;
  showLoading('Analyzing multi-factor interrelations for ' + symbol + '...');

  try {
    const res = await fetch(`/api/analyze/${encodeURIComponent(symbol)}?period=${state.currentPeriod}`);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || `Server returned ${res.status}`);
    }

    state.data = await res.json();

    // Build factor map
    state.factorMap = buildFactorMap(state.data);
    state.sortedDates = Object.keys(state.factorMap).sort();

    // Render everything
    updateStockBanner();
    renderMainChart();
    renderOverlayChart();
    renderCorrelationChart();
    renderOverallCorrelations();
    renderHighlights();
    renderEarnings();
    updateSimulatorBetas();

    // Reset simulator sliders to 0 and compute default
    applyPreset('reset');

    // Show initial snapshot for latest date
    if (state.sortedDates.length > 0) {
      const latestDate = state.sortedDates[state.sortedDates.length - 1];
      showSnapshotForDate(latestDate);
    }

  } catch (err) {
    console.error('Analysis error:', err);
    alert('Error: ' + err.message);
  } finally {
    hideLoading();
  }
}


// ===================================================================
// FACTOR MAP BUILDER
// ===================================================================

function buildFactorMap(data) {
  const map = {};

  const factorLookups = {};
  for (const [key, values] of Object.entries(data.factors || {})) {
    factorLookups[key] = {};
    for (const item of values) {
      factorLookups[key][item.date] = item.value;
    }
  }

  const lastFactors = { usdinr: null, gold: null, silver: null, oil: null };
  const allDates = (data.stock || []).map(s => s.date).sort();

  for (const date of allDates) {
    const stockPoint = data.stock.find(s => s.date === date);
    const entry = { stock: stockPoint ? stockPoint.close : null };

    for (const key of Object.keys(FACTORS)) {
      if (factorLookups[key]?.[date] != null) {
        entry[key] = factorLookups[key][date];
        lastFactors[key] = entry[key];
      } else {
        entry[key] = lastFactors[key];
      }
    }

    map[date] = entry;
  }

  return map;
}


// ===================================================================
// MAIN CHART (TradingView Lightweight Charts)
// ===================================================================

function renderMainChart() {
  const container = document.getElementById('main-chart');
  container.innerHTML = '';

  state.mainChart = LightweightCharts.createChart(container, {
    width: container.clientWidth,
    height: 420,
    layout: {
      background: { color: '#1c2030' },
      textColor: '#d1d4dc',
    },
    grid: {
      vertLines: { color: '#1e222d' },
      horzLines: { color: '#1e222d' },
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
    },
    rightPriceScale: {
      borderColor: '#1e222d',
    },
    timeScale: {
      borderColor: '#1e222d',
      timeVisible: false,
    },
  });

  // Area series for stock price (worm graph)
  state.stockSeries = state.mainChart.addAreaSeries({
    topColor: 'rgba(41, 98, 255, 0.45)',
    bottomColor: 'rgba(41, 98, 255, 0.02)',
    lineColor: '#2962ff',
    lineWidth: 2,
  });

  const chartData = (state.data.stock || [])
    .filter(d => d.date && Number.isFinite(d.close))
    .map(d => ({ time: d.date, value: d.close }))
    .sort((a, b) => a.time.localeCompare(b.time));
  state.stockSeries.setData(chartData);

  // Markers for ATH, ATL, and Earnings
  const markerMap = new Map(); // date -> marker to prevent duplicate times
  const highlights = state.data.highlights || {};
  const stockDateSet = new Set(chartData.map(d => d.time));

  if (highlights.allTimeHigh && stockDateSet.has(highlights.allTimeHigh.date)) {
    markerMap.set(highlights.allTimeHigh.date, {
      time: highlights.allTimeHigh.date,
      position: 'aboveBar',
      color: '#26a69a',
      shape: 'arrowDown',
      text: '🏆 ATH: ' + formatCurrency(highlights.allTimeHigh.close, state.data.currency),
    });
  }
  if (highlights.allTimeLow && stockDateSet.has(highlights.allTimeLow.date)) {
    markerMap.set(highlights.allTimeLow.date, {
      time: highlights.allTimeLow.date,
      position: 'belowBar',
      color: '#ef5350',
      shape: 'arrowUp',
      text: '🔻 ATL: ' + formatCurrency(highlights.allTimeLow.close, state.data.currency),
    });
  }

  // Quarterly Earnings markers (only if not already marked by ATH/ATL)
  const earnings = state.data.earnings || [];
  for (const earn of earnings) {
    if (earn.date && stockDateSet.has(earn.date) && !markerMap.has(earn.date)) {
      const beat = earn.surprisePct != null && earn.surprisePct >= 0;
      markerMap.set(earn.date, {
        time: earn.date,
        position: 'aboveBar',
        color: beat ? '#ffca28' : '#ff7043',
        shape: 'circle',
        text: '📅 Results' + (earn.surprisePct != null ? ` (${earn.surprisePct > 0 ? '+' : ''}${earn.surprisePct}%)` : ''),
      });
    }
  }

  const markers = Array.from(markerMap.values()).sort((a, b) => a.time.localeCompare(b.time));
  if (markers.length) {
    state.stockSeries.setMarkers(markers);
  }

  // Crosshair move -> update snapshot
  state.mainChart.subscribeCrosshairMove(handleCrosshairMove);

  // Click on chart -> pin/focus snapshot date
  state.mainChart.subscribeClick(param => {
    if (param.time) {
      const dateStr = formatLWCTime(param.time);
      showSnapshotForDate(dateStr, true);
    }
  });

  // Responsive resize
  const ro = new ResizeObserver(entries => {
    if (state.mainChart) {
      state.mainChart.applyOptions({ width: entries[0].contentRect.width });
    }
  });
  ro.observe(container);

  state.mainChart.timeScale().fitContent();
}


// ===================================================================
// CROSSHAIR HANDLER
// ===================================================================

function handleCrosshairMove(param) {
  if (!param.time || !param.point) {
    return;
  }
  const dateStr = formatLWCTime(param.time);
  showSnapshotForDate(dateStr, false);
}

function showSnapshotForDate(dateStr, fetchNewsImmediately = false) {
  const factors = state.factorMap[dateStr];
  if (!factors) return;

  document.getElementById('snapshot-content').classList.remove('hidden');
  document.querySelector('#snapshot-card .hint-text').classList.add('hidden');

  document.getElementById('snap-date').textContent = formatDisplayDate(dateStr);

  // Stock price & change
  document.getElementById('snap-stock').textContent =
    factors.stock != null ? formatCurrency(factors.stock, state.data.currency) : '---';
  updateChangeIndicator('snap-stock-chg', dateStr, 'stock');

  // Factors
  for (const [key, config] of Object.entries(FACTORS)) {
    const val = factors[key];
    document.getElementById(`snap-${key}`).textContent =
      val != null ? config.prefix + formatNumber(val) : 'N/A';
    updateChangeIndicator(`snap-${key}-chg`, dateStr, key);
  }

  // Correlation arrows
  updateCorrelationArrows(dateStr);

  // Targeted news fetch
  if (fetchNewsImmediately) {
    clearTimeout(state.newsDebounceTimer);
    state.lastNewsDate = dateStr;
    fetchNews(dateStr);
  } else {
    debouncedFetchNews(dateStr);
  }
}

function jumpToDate(dateStr) {
  if (!dateStr || !state.factorMap[dateStr]) {
    // If exact date not found, find nearest date
    const targetTime = new Date(dateStr).getTime();
    let closest = state.sortedDates[0];
    let minDiff = Infinity;
    for (const d of state.sortedDates) {
      const diff = Math.abs(new Date(d).getTime() - targetTime);
      if (diff < minDiff) {
        minDiff = diff;
        closest = d;
      }
    }
    dateStr = closest;
  }

  showSnapshotForDate(dateStr, true);

  // Highlight card pulse
  const snapCard = document.getElementById('snapshot-card');
  snapCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}


// ===================================================================
// CHANGE INDICATOR
// ===================================================================

function updateChangeIndicator(elementId, dateStr, factorKey) {
  const el = document.getElementById(elementId);
  if (!el) return;

  const idx = state.sortedDates.indexOf(dateStr);
  if (idx <= 0) {
    el.textContent = '---';
    el.className = 'factor-change';
    return;
  }

  const prevDate = state.sortedDates[idx - 1];
  const currVal = state.factorMap[dateStr]?.[factorKey];
  const prevVal = state.factorMap[prevDate]?.[factorKey];

  if (currVal == null || prevVal == null || prevVal === 0) {
    el.textContent = '---';
    el.className = 'factor-change';
    return;
  }

  const pctChange = ((currVal - prevVal) / prevVal) * 100;
  const sign = pctChange >= 0 ? '+' : '';
  el.textContent = sign + pctChange.toFixed(2) + '%';
  el.className = 'factor-change ' + (pctChange >= 0 ? 'positive' : 'negative');
}


// ===================================================================
// CORRELATION ARROWS
// ===================================================================

function updateCorrelationArrows(dateStr) {
  const container = document.getElementById('snap-arrows');
  const idx = state.sortedDates.indexOf(dateStr);

  if (idx <= 0) {
    container.innerHTML = '<span class="hint-text">First trading day of period</span>';
    return;
  }

  const prevDate = state.sortedDates[idx - 1];
  const curr = state.factorMap[dateStr];
  const prev = state.factorMap[prevDate];

  if (!curr || !prev) {
    container.innerHTML = '';
    return;
  }

  const stockDir = (curr.stock || 0) - (prev.stock || 0);
  let html = '';

  for (const [key, config] of Object.entries(FACTORS)) {
    const factorDir = (curr[key] || 0) - (prev[key] || 0);
    const sameDirection = (stockDir >= 0 && factorDir >= 0) || (stockDir < 0 && factorDir < 0);
    const arrows = sameDirection ? '↑↑ Co-Move' : '↑↓ Divergent';
    const color = sameDirection ? '#26a69a' : '#ef5350';

    html += `<span class="corr-arrow" style="color: ${color};">${config.icon} ${arrows}</span>`;
  }

  container.innerHTML = html;
}


// ===================================================================
// NEWS FETCHING
// ===================================================================

function debouncedFetchNews(dateStr) {
  if (state.lastNewsDate === dateStr) return;

  clearTimeout(state.newsDebounceTimer);
  state.newsDebounceTimer = setTimeout(() => {
    state.lastNewsDate = dateStr;
    fetchNews(dateStr);
  }, 400);
}

async function fetchNews(dateStr) {
  const container = document.getElementById('news-content');
  const hint = document.querySelector('#news-card .hint-text');

  const companyName = state.data?.name || state.currentSymbol.replace('.NS', '').replace('.BO', '');

  hint.classList.add('hidden');
  container.innerHTML = '<p class="hint-text">Fetching news around ' + dateStr + '...</p>';

  try {
    const res = await fetch(`/api/news?q=${encodeURIComponent(companyName)}&date=${dateStr}`);
    if (!res.ok) throw new Error('News fetch failed');
    const data = await res.json();
    const articles = Array.isArray(data) ? data : (data.articles || []);

    if (!articles.length) {
      container.innerHTML = `<p class="news-empty">No major headlines recorded around ${dateStr}.</p>`;
      return;
    }

    container.innerHTML = articles.slice(0, 5).map(a => `
      <div class="news-item" onclick="window.open('${escapeHtml(a.url || '#')}', '_blank')">
        <div class="news-title">${escapeHtml(a.title)}</div>
        <div class="news-source">${escapeHtml(a.source || 'News')} <span class="news-date">${escapeHtml(a.date || '')}</span></div>
      </div>
    `).join('');
  } catch (err) {
    console.error('News error:', err);
    container.innerHTML = '<p class="news-empty">Could not load news headlines.</p>';
  }
}


// ===================================================================
// OVERLAY CHART (Normalized Factor Comparison)
// ===================================================================

function renderOverlayChart() {
  const container = document.getElementById('overlay-chart');
  container.innerHTML = '';

  state.overlayChart = LightweightCharts.createChart(container, {
    width: container.clientWidth,
    height: 220,
    layout: {
      background: { color: '#1c2030' },
      textColor: '#d1d4dc',
    },
    grid: {
      vertLines: { color: '#1e222d' },
      horzLines: { color: '#1e222d' },
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
    },
    rightPriceScale: {
      borderColor: '#1e222d',
    },
    timeScale: {
      borderColor: '#1e222d',
      timeVisible: false,
    },
  });

  const allKeys = [...Object.keys(FACTORS), 'stock'];
  const minMax = {};

  for (const key of allKeys) {
    let min = Infinity, max = -Infinity;
    for (const date of state.sortedDates) {
      const val = state.factorMap[date]?.[key];
      if (val != null && Number.isFinite(val)) {
        if (val < min) min = val;
        if (val > max) max = val;
      }
    }
    minMax[key] = {
      min: Number.isFinite(min) ? min : 0,
      max: Number.isFinite(max) ? max : 100,
    };
  }

  const normalize = (val, key) => {
    if (val == null || !Number.isFinite(val)) return null;
    const { min, max } = minMax[key];
    if (max <= min) return 50;
    const norm = ((val - min) / (max - min)) * 100;
    return Number.isFinite(norm) ? Math.max(0, Math.min(100, norm)) : 50;
  };

  state.overlaySeries = {};

  // Stock normalized line
  const stockOverlay = state.overlayChart.addLineSeries({
    color: '#2962ff',
    lineWidth: 2.2,
    priceLineVisible: false,
    lastValueVisible: false,
    title: 'Stock',
  });

  const stockData = state.sortedDates
    .filter(d => state.factorMap[d]?.stock != null && Number.isFinite(state.factorMap[d].stock))
    .map(d => ({
      time: d,
      value: normalize(state.factorMap[d].stock, 'stock'),
    }))
    .filter(d => d.value !== null && Number.isFinite(d.value));

  stockOverlay.setData(stockData);
  state.overlaySeries.stock = stockOverlay;

  // Factor normalized lines
  for (const [key, config] of Object.entries(FACTORS)) {
    const series = state.overlayChart.addLineSeries({
      color: config.color,
      lineWidth: 1.5,
      priceLineVisible: false,
      lastValueVisible: false,
      title: config.label,
    });

    const data = state.sortedDates
      .filter(d => state.factorMap[d]?.[key] != null && Number.isFinite(state.factorMap[d][key]))
      .map(d => ({
        time: d,
        value: normalize(state.factorMap[d][key], key),
      }))
      .filter(d => d.value !== null && Number.isFinite(d.value));

    series.setData(data);
    state.overlaySeries[key] = series;
  }

  state.overlayChart.subscribeCrosshairMove(handleCrosshairMove);

  const ro = new ResizeObserver(entries => {
    if (state.overlayChart) {
      state.overlayChart.applyOptions({ width: entries[0].contentRect.width });
    }
  });
  ro.observe(container);

  state.overlayChart.timeScale().fitContent();

  // Apply checkboxes
  const toggleMap = {
    'toggle-usdinr': 'usdinr',
    'toggle-gold': 'gold',
    'toggle-silver': 'silver',
    'toggle-oil': 'oil',
    'toggle-stock': 'stock',
  };
  for (const [id, key] of Object.entries(toggleMap)) {
    const el = document.getElementById(id);
    if (el && state.overlaySeries[key]) {
      state.overlaySeries[key].applyOptions({ visible: el.checked });
    }
  }
}


// ===================================================================
// ROLLING CORRELATION CHART (Chart.js)
// ===================================================================

function renderCorrelationChart() {
  const canvas = document.getElementById('correlation-chart');
  const ctx = canvas.getContext('2d');

  if (state.corrChart) {
    state.corrChart.destroy();
    state.corrChart = null;
  }

  const rollCorr = state.data.rollingCorrelations || {};
  const factorKeys = Object.keys(FACTORS).filter(k => rollCorr[k] && rollCorr[k].length > 0);

  if (factorKeys.length === 0) return;

  // Collect union of all sorted dates across factors for strictly aligned X-axis
  const dateSet = new Set();
  for (const k of factorKeys) {
    for (const pt of rollCorr[k]) {
      if (pt.date && Number.isFinite(pt.value)) {
        dateSet.add(pt.date);
      }
    }
  }
  const allLabels = Array.from(dateSet).sort();

  if (allLabels.length === 0) return;

  // Build aligned dataset for each factor
  const datasets = factorKeys.map(key => {
    const valByDate = new Map();
    for (const pt of rollCorr[key]) {
      if (pt.date && Number.isFinite(pt.value)) {
        valByDate.set(pt.date, Math.max(-1, Math.min(1, pt.value)));
      }
    }

    return {
      label: FACTORS[key].label,
      data: allLabels.map(d => valByDate.has(d) ? valByDate.get(d) : null),
      borderColor: FACTORS[key].color,
      borderWidth: 1.6,
      pointRadius: 0,
      tension: 0.2,
      spanGaps: true,
      fill: false,
    };
  });

  state.corrChart = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      scales: {
        x: {
          type: 'category',
          ticks: {
            color: '#787b86',
            maxTicksLimit: 8,
            font: { size: 9 },
          },
          grid: { color: '#1e222d' },
        },
        y: {
          min: -1,
          max: 1,
          ticks: {
            color: '#787b86',
            font: { size: 9 },
            stepSize: 0.5,
          },
          grid: { color: '#1e222d' },
        },
      },
      plugins: {
        legend: {
          labels: {
            color: '#d1d4dc',
            font: { size: 10 },
            usePointStyle: true,
            boxWidth: 8,
          },
        },
        tooltip: {
          backgroundColor: '#1c2030',
          titleColor: '#d1d4dc',
          bodyColor: '#d1d4dc',
          borderColor: '#1e222d',
          borderWidth: 1,
        },
      },
      layout: { padding: { top: 4, bottom: 4 } },
    },
  });
}


// ===================================================================
// STATISTICAL CORRELATIONS (Right Panel)
// ===================================================================

function renderOverallCorrelations() {
  const container = document.getElementById('overall-correlations');
  const corr = state.data.correlations || {};

  let html = '';
  for (const [key, config] of Object.entries(FACTORS)) {
    const val = corr[key] != null ? corr[key] : 0;
    const pct = Math.abs(val) * 100;
    const isPositive = val >= 0;
    const barColor = isPositive ? '#26a69a' : '#ef5350';
    const direction = isPositive ? '↑↑ Direct' : '↑↓ Inverse';

    html += `
      <div style="margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 3px;">
          <span style="color: #d1d4dc;">${config.icon} ${config.label}</span>
          <span style="color: ${barColor}; font-weight: 700;">${direction} (${val.toFixed(2)})</span>
        </div>
        <div class="corr-bar-container">
          <div class="corr-bar" style="width: ${pct}%; background: ${barColor};"></div>
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
}


// ===================================================================
// HIGHLIGHTS (ATH / ATL)
// ===================================================================

function renderHighlights() {
  const container = document.getElementById('highlights-content');
  const highlights = state.data.highlights || {};
  const { allTimeHigh, allTimeLow } = highlights;

  let html = '';

  if (allTimeHigh) {
    html += `
      <div class="highlight-item" onclick="jumpToDate('${allTimeHigh.date}')" title="Click to view macro factors on ATH date">
        <div class="highlight-label">🏆 Lifetime Highest Price</div>
        <div class="highlight-price" style="color: #26a69a;">
          ${formatCurrency(allTimeHigh.close, state.data.currency)}
        </div>
        <div class="highlight-date">Date: <b>${formatDisplayDate(allTimeHigh.date)}</b></div>
        <div class="highlight-factors">
          ${Object.entries(allTimeHigh.factors || {}).map(([k, v]) =>
            `${FACTORS[k]?.icon || ''} ${FACTORS[k]?.label || k}: <b>${FACTORS[k]?.prefix || ''}${formatNumber(v)}</b>`
          ).join(' &nbsp;•&nbsp; ')}
        </div>
        <span class="highlight-action-hint">👉 Click to inspect factors &amp; news on this date</span>
      </div>
    `;
  }

  if (allTimeLow) {
    html += `
      <div class="highlight-item" onclick="jumpToDate('${allTimeLow.date}')" title="Click to view macro factors on ATL date">
        <div class="highlight-label">🔻 Lifetime Lowest Price</div>
        <div class="highlight-price" style="color: #ef5350;">
          ${formatCurrency(allTimeLow.close, state.data.currency)}
        </div>
        <div class="highlight-date">Date: <b>${formatDisplayDate(allTimeLow.date)}</b></div>
        <div class="highlight-factors">
          ${Object.entries(allTimeLow.factors || {}).map(([k, v]) =>
            `${FACTORS[k]?.icon || ''} ${FACTORS[k]?.label || k}: <b>${FACTORS[k]?.prefix || ''}${formatNumber(v)}</b>`
          ).join(' &nbsp;•&nbsp; ')}
        </div>
        <span class="highlight-action-hint">👉 Click to inspect factors &amp; news on this date</span>
      </div>
    `;
  }

  if (!html) {
    html = '<p class="hint-text">No highlight data available.</p>';
  }

  container.innerHTML = html;
}


// ===================================================================
// QUARTERLY RESULTS (EARNINGS)
// ===================================================================

function renderEarnings() {
  const container = document.getElementById('earnings-content');
  const earnings = state.data.earnings || [];

  if (!earnings.length) {
    container.innerHTML = '<p class="hint-text">No earnings records found for this ticker.</p>';
    return;
  }

  // Display top 4 past earnings results
  const pastEarnings = earnings.filter(e => e.reportedEPS != null).slice(-4).reverse();

  if (!pastEarnings.length) {
    container.innerHTML = '<p class="hint-text">Upcoming earnings scheduled.</p>';
    return;
  }

  container.innerHTML = pastEarnings.map(e => {
    const isBeat = e.surprisePct != null && e.surprisePct >= 0;
    const badgeClass = isBeat ? 'surprise-positive' : 'surprise-negative';
    const surpriseText = e.surprisePct != null
      ? `${e.surprisePct > 0 ? '+' : ''}${e.surprisePct.toFixed(1)}% ${isBeat ? 'Beat' : 'Miss'}`
      : 'Reported';

    return `
      <div class="earnings-item" onclick="jumpToDate('${e.date}')" title="Click to inspect market factors on this earnings date">
        <div class="earnings-header">
          <span class="earnings-date">📅 ${formatDisplayDate(e.date)}</span>
          <span class="earnings-surprise ${badgeClass}">${surpriseText}</span>
        </div>
        <div class="earnings-details">
          <span>Reported EPS: <b>₹${e.reportedEPS}</b></span>
          ${e.epsEstimate != null ? `<span>Est: <b>₹${e.epsEstimate}</b></span>` : ''}
        </div>
        <span class="highlight-action-hint">👉 Inspect reaction on this earnings date</span>
      </div>
    `;
  }).join('');
}


// ===================================================================
// FUTURE WHAT-IF SCENARIO SIMULATOR
// ===================================================================

function initSimulatorControls() {
  const sliders = ['sim-usdinr', 'sim-oil', 'sim-gold', 'sim-silver'];
  for (const id of sliders) {
    const slider = document.getElementById(id);
    if (slider) {
      slider.addEventListener('input', () => {
        const factorKey = id.replace('sim-', '');
        document.getElementById(`val-${id}`).textContent =
          (slider.value > 0 ? '+' : '') + parseFloat(slider.value).toFixed(1) + '%';
        recalculateSimulation();
      });
    }
  }
}

function updateSimulatorBetas() {
  const sens = state.data?.sensitivities || {};
  document.getElementById('beta-usdinr').textContent = (sens.usdinr != null ? sens.usdinr.toFixed(3) : '0.00');
  document.getElementById('beta-oil').textContent = (sens.oil != null ? sens.oil.toFixed(3) : '0.00');
  document.getElementById('beta-gold').textContent = (sens.gold != null ? sens.gold.toFixed(3) : '0.00');
  document.getElementById('beta-silver').textContent = (sens.silver != null ? sens.silver.toFixed(3) : '0.00');
}

function recalculateSimulation() {
  if (!state.data) return;

  const currentPrice = state.data.currentPrice || 0;
  const sens = state.data.sensitivities || {};

  const usdShift = parseFloat(document.getElementById('sim-usdinr').value) || 0;
  const oilShift = parseFloat(document.getElementById('sim-oil').value) || 0;
  const goldShift = parseFloat(document.getElementById('sim-gold').value) || 0;
  const silverShift = parseFloat(document.getElementById('sim-silver').value) || 0;

  const b_usd = sens.usdinr || 0;
  const b_oil = sens.oil || 0;
  const b_gold = sens.gold || 0;
  const b_silver = sens.silver || 0;

  const imp_usd = usdShift * b_usd;
  const imp_oil = oilShift * b_oil;
  const imp_gold = goldShift * b_gold;
  const imp_silver = silverShift * b_silver;

  const totalDeltaPct = imp_usd + imp_oil + imp_gold + imp_silver;
  const projectedPrice = currentPrice * (1 + totalDeltaPct / 100);

  // Update output displays
  document.getElementById('sim-projected-price').textContent = formatCurrency(projectedPrice, state.data.currency);

  const deltaEl = document.getElementById('sim-projected-delta');
  const sign = totalDeltaPct >= 0 ? '+' : '';
  deltaEl.textContent = `${sign}${totalDeltaPct.toFixed(2)}% (${sign}${formatCurrency(projectedPrice - currentPrice, state.data.currency)})`;
  deltaEl.className = 'sim-result-delta ' + (totalDeltaPct >= 0 ? 'positive' : 'negative');

  // Breakdown details
  document.getElementById('sim-breakdown').innerHTML = `
    <div class="sim-breakdown-row"><span>USD/INR Impact:</span> <b>${imp_usd >= 0 ? '+' : ''}${imp_usd.toFixed(2)}%</b></div>
    <div class="sim-breakdown-row"><span>Crude Oil Impact:</span> <b>${imp_oil >= 0 ? '+' : ''}${imp_oil.toFixed(2)}%</b></div>
    <div class="sim-breakdown-row"><span>Gold Impact:</span> <b>${imp_gold >= 0 ? '+' : ''}${imp_gold.toFixed(2)}%</b></div>
    <div class="sim-breakdown-row"><span>Silver Impact:</span> <b>${imp_silver >= 0 ? '+' : ''}${imp_silver.toFixed(2)}%</b></div>
  `;
}

function applyPreset(presetType) {
  const sUsd = document.getElementById('sim-usdinr');
  const sOil = document.getElementById('sim-oil');
  const sGold = document.getElementById('sim-gold');
  const sSilver = document.getElementById('sim-silver');

  if (presetType === 'oilShock') {
    sOil.value = 15;
    sUsd.value = 1.5;
    sGold.value = 0;
    sSilver.value = 0;
  } else if (presetType === 'rupeeWeak') {
    sUsd.value = 5;
    sOil.value = 0;
    sGold.value = 2;
    sSilver.value = 0;
  } else if (presetType === 'goldRally') {
    sGold.value = 10;
    sSilver.value = 8;
    sUsd.value = 0;
    sOil.value = -3;
  } else {
    // Reset
    sUsd.value = 0;
    sOil.value = 0;
    sGold.value = 0;
    sSilver.value = 0;
  }

  // Update label texts
  document.getElementById('val-sim-usdinr').textContent = (sUsd.value > 0 ? '+' : '') + sUsd.value + '%';
  document.getElementById('val-sim-oil').textContent = (sOil.value > 0 ? '+' : '') + sOil.value + '%';
  document.getElementById('val-sim-gold').textContent = (sGold.value > 0 ? '+' : '') + sGold.value + '%';
  document.getElementById('val-sim-silver').textContent = (sSilver.value > 0 ? '+' : '') + sSilver.value + '%';

  recalculateSimulation();
}

window.applyPreset = applyPreset;
window.jumpToDate = jumpToDate;


// ===================================================================
// STOCK BANNER
// ===================================================================

function updateStockBanner() {
  const banner = document.getElementById('stock-banner');
  const data = state.data;

  if (!data) {
    banner.classList.add('hidden');
    return;
  }

  document.getElementById('stock-name').textContent = data.name || state.currentSymbol;
  document.getElementById('stock-symbol-badge').textContent = state.currentSymbol;
  document.getElementById('stock-currency-badge').textContent = data.currency || 'INR';
  document.getElementById('stock-sector-badge').textContent = data.sector || 'Equities';

  if (data.currentPrice) {
    document.getElementById('stock-live-price').textContent = formatCurrency(data.currentPrice, data.currency);
  }

  banner.classList.remove('hidden');
}


// ===================================================================
// HELPER FUNCTIONS
// ===================================================================

function formatCurrency(val, currency) {
  if (val == null) return '---';
  if (currency === 'INR') {
    return '₹' + val.toLocaleString('en-IN', { maximumFractionDigits: 2 });
  }
  return '$' + val.toLocaleString('en-US', { maximumFractionDigits: 2 });
}

function formatNumber(val) {
  if (val == null) return '---';
  return val.toLocaleString('en-US', { maximumFractionDigits: 2 });
}

function formatDisplayDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-IN', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatLWCTime(time) {
  if (typeof time === 'string') return time;
  if (time && time.year) {
    return `${time.year}-${String(time.month).padStart(2, '0')}-${String(time.day).padStart(2, '0')}`;
  }
  const d = new Date(time * 1000);
  return d.toISOString().split('T')[0];
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function showLoading(msg) {
  const overlay = document.getElementById('loading-overlay');
  const text = document.getElementById('loading-text');
  text.textContent = msg || 'Loading...';
  overlay.classList.remove('hidden');
}

function hideLoading() {
  document.getElementById('loading-overlay').classList.add('hidden');
}
