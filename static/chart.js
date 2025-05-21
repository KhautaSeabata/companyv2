let chart = null;
const ctx = document.getElementById("chartCanvas").getContext("2d");
const statusEl = document.getElementById("status");
const chartTypeSelect = document.getElementById("chart-type");

let lastTickEpoch = null;
let lastCandleTime = null;

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

async function fetchTicks() {
  const res = await fetch("/api/ticks");
  const data = await res.json();
  return data;
}

async function fetchCandles() {
  const res = await fetch("/api/1minVix25");
  const data = await res.json();
  return data;
}

function createLineChart(ticks) {
  if (chart) chart.destroy();

  const labels = ticks.map(t => formatTime(new Date(t.epoch * 1000)));
  const prices = ticks.map(t => t.quote);

  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'R_25 Price',
        data: prices,
        borderColor: '#00e676',
        backgroundColor: 'rgba(0, 230, 118, 0.2)',
        fill: true,
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 0
      }]
    },
    options: {
      responsive: true,
      animation: false,
      scales: {
        x: {
          ticks: { color: "#aaa" },
          grid: { color: "#333" }
        },
        y: {
          ticks: { color: "#aaa" },
          grid: { color: "#333" }
        }
      },
      plugins: {
        legend: { labels: { color: "#fff" } }
      }
    }
  });
}

function createCandlestickChart(candles) {
  if (chart) chart.destroy();

  const data = candles.map(c => ({
    x: new Date(c.time * 1000),
    o: c.open,
    h: c.high,
    l: c.low,
    c: c.close
  }));

  chart = new Chart(ctx, {
    type: 'candlestick',
    data: {
      datasets: [{
        label: 'R_25 1-min OHLC',
        data: data,
        color: {
          up: '#00ff00',
          down: '#ff0000',
          unchanged: '#999'
        }
      }]
    },
    options: {
      responsive: true,
      animation: false,
      scales: {
        x: {
          type: 'time',
          time: {
            tooltipFormat: 'MMM dd, HH:mm',
            unit: 'minute',
            displayFormats: {
              minute: 'HH:mm'
            }
          },
          ticks: { color: "#aaa" },
          grid: { color: "#333" }
        },
        y: {
          ticks: { color: "#aaa" },
          grid: { color: "#333" }
        }
      },
      plugins: {
        legend: { labels: { color: "#fff" } },
        tooltip: {
          enabled: true,
          mode: 'nearest',
          intersect: false,
          callbacks: {
            label: function(context) {
              const o = context.raw.o;
              const h = context.raw.h;
              const l = context.raw.l;
              const c = context.raw.c;
              return `O: ${o}  H: ${h}  L: ${l}  C: ${c}`;
            }
          }
        }
      }
    }
  });
}

async function updateLineChart() {
  const ticks = await fetchTicks();
  if (!ticks.length) {
    statusEl.textContent = "⚠️ No tick data found";
    return;
  }

  // Only update if new data available
  const newestEpoch = ticks[ticks.length -1].epoch;
  if (lastTickEpoch === newestEpoch) return;

  lastTickEpoch = newestEpoch;

  createLineChart(ticks);
  statusEl.textContent = "✅ Connected & Live (Line Chart)";
}

async function updateCandlestickChart() {
  const candles = await fetchCandles();
  if (!candles.length) {
    statusEl.textContent = "⚠️ No OHLC data found";
    return;
  }

  // Only update if new candle available
  const newestTime = candles[candles.length -1].time;
  if (lastCandleTime === newestTime) return;

  lastCandleTime = newestTime;

  createCandlestickChart(candles);
  statusEl.textContent = "✅ Connected & Live (Candlestick Chart)";
}

async function refreshChart() {
  const chartType = chartTypeSelect.value;
  if (chartType === "line") {
    await updateLineChart();
  } else {
    await updateCandlestickChart();
  }
}

// Initial load & polling every 1 sec
async function init() {
  await refreshChart();
  setInterval(refreshChart, 1000);
}

chartTypeSelect.addEventListener("change", async () => {
  lastTickEpoch = null;
  lastCandleTime = null;
  await refreshChart();
});

init();
