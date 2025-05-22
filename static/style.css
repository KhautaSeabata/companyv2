// Firebase init
const firebaseConfig = {
  databaseURL: "https://company-bdb78-default-rtdb.firebaseio.com"
};
firebase.initializeApp(firebaseConfig);
const db = firebase.database();

let chart;
let allTicks = [];
let maxTicksToShow = 100;

const signalList = document.getElementById("signal-list");
const tickRange = document.getElementById("tickRange");

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

function updateChart() {
  const displayTicks = allTicks.slice(-maxTicksToShow);
  chart.data.labels = displayTicks.map(t => new Date(t.epoch * 1000));
  chart.data.datasets[0].data = displayTicks.map(t => t.quote);
  chart.update();
}

function listenToFirebase() {
  const ref = db.ref("ticks/R_25").orderByChild("epoch").limitToLast(900);
  ref.on("value", (snapshot) => {
    const data = snapshot.val();
    if (!data) return;
    allTicks = Object.values(data).sort((a, b) => a.epoch - b.epoch);
    updateChart();
  });
}

window.onload = () => {
  createChart();
  listenToFirebase();
  tickRange.addEventListener("change", () => {
    maxTicksToShow = parseInt(tickRange.value);
    updateChart();
  });
};
