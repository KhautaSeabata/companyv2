let chart;
const signalList = document.getElementById("signal-list");

function createChart() {
  const ctx = document.getElementById("lineChart").getContext("2d");
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        label: "Vix25 Price",
        data: [],
        borderColor: "#0ff",
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
      }]
    },
    options: {
      responsive: true,
      animation: false,
      scales: {
        x: {
          type: 'time',
          time: {
            tooltipFormat: 'HH:mm:ss',
            unit: 'second',
            displayFormats: { second: 'HH:mm:ss' }
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
        legend: { labels: { color: "#0ff" } }
      }
    }
  });
}

function updateChart(ticks) {
  if (!ticks || ticks.length === 0) return;
  chart.data.labels = ticks.map(t => new Date(t.epoch * 1000));
  chart.data.datasets[0].data = ticks.map(t => t.quote);
  chart.update();
}

function displaySignal(signal) {
  if (!signalList) return;
  if (!signal) return;
  const html = `
    <div class="signal">
      <b>Pattern:</b> ${signal.pattern} <br />
      <b>Entry:</b> ${signal.entry} <br />
      <b>TP:</b> ${signal.tp} <br />
      <b>SL:</b> ${signal.sl} <br />
      <b>Signal Time (JHB):</b> ${new Date(signal.time * 1000).toLocaleString('en-ZA', { timeZone: 'Africa/Johannesburg', hour12: false })} <br />
      <b>Status:</b> ${signal.status || 'Active'}
    </div>
  `;
  // Insert new signals on top
  signalList.insertAdjacentHTML('afterbegin', html);
}

function connectWebSocket() {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${protocol}://${location.host}/ws`);

  ws.onopen = () => {
    console.log("WebSocket connected");
  };

  ws.onclose = () => {
    console.log("WebSocket disconnected");
    signalList.innerHTML = "<b>Disconnected from server</b>";
  };

  ws.onerror = (e) => {
    console.error("WebSocket error:", e);
    signalList.innerHTML = "<b>WebSocket error occurred</b>";
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.ticks) {
      updateChart(msg.ticks);
    }
    if (msg.signal) {
      displaySignal(msg.signal);
    }
  };
}

window.onload = () => {
  createChart();
  connectWebSocket();
};
