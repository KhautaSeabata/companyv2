let chart;
const indexSelect = document.getElementById("index-select");
const tfSelect = document.getElementById("tf-select");
const connStatus = document.getElementById("connection-status");

function createChart() {
  const ctx = document.getElementById("chart").getContext("2d");
  chart = new Chart(ctx, {
    type: 'candlestick',
    data: { datasets: [{ label: 'Candles', data: [] }] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: { ticks: { color: "#aaa" }, grid: { color: "#333" } },
        y: { ticks: { color: "#aaa" }, grid: { color: "#333" } }
      },
      plugins: {
        legend: { labels: { color: "#0f0" } }
      }
    }
  });
}

function updateChart(candles) {
  chart.data.datasets[0].data = candles.map(c => ({
    x: new Date(c.time * 1000),
    o: c.open,
    h: c.high,
    l: c.low,
    c: c.close,
  }));
  chart.update();
  setTimeout(() => {
    chart.canvas.parentNode.scrollLeft = chart.canvas.scrollWidth;
  }, 100);
}

function connectSocket(index, tf) {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${location.host}/ws/${index}/${tf}`);

  socket.onopen = () => {
    connStatus.textContent = "Connected";
    connStatus.classList.remove("disconnected");
  };

  socket.onclose = () => {
    connStatus.textContent = "Disconnected";
    connStatus.classList.add("disconnected");
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.candles) {
      updateChart(data.candles);
    }
  };
}

function init() {
  createChart();
  connectSocket(indexSelect.value, tfSelect.value);

  indexSelect.addEventListener("change", () => location.reload());
  tfSelect.addEventListener("change", () => location.reload());
}

window.onload = init;
