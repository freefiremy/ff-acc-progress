const REMOTE_BASE = 'https://raw.githubusercontent.com/rasikasrimal/ff-acc-progress/main';\nconst PLAYERS = [
  {
    uid: "2805365702",
    label: "Main Account",
    description: "Full progress tracking (XP, BR score, likes).",
  },
  {
    uid: "667352678",
    label: "Likes Automation",
    description: "Likes-only automation target.",
  },
];

const MONTH_INDEX = {
  January: "01",
  February: "02",
  March: "03",
  April: "04",
  May: "05",
  June: "06",
  July: "07",
  August: "08",
  September: "09",
  October: "10",
  November: "11",
  December: "12",
};

async function loadCsv(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  const text = await response.text();
  const parsed = Papa.parse(text, {
    header: true,
    skipEmptyLines: true,
  });
  return parsed.data;
}

function formatNumber(value) {
  if (value === null || value === undefined || value === "") return "-";
  const num = Number(value);
  if (Number.isNaN(num)) return value;
  return num.toLocaleString();
}

function getLatestMonth(summaryRows) {
  const monthRows = summaryRows.filter((row) => row.Month && row.Month !== "ALL");
  if (!monthRows.length) return null;
  const last = monthRows[monthRows.length - 1];
  const monthNumber = MONTH_INDEX[last.Month] || "01";
  return {
    year: last.Year,
    monthName: last.Month,
    monthNumber,
  };
}

function renderNav(players) {
  const nav = document.getElementById("player-nav");
  players.forEach((player) => {
    const link = document.createElement("a");
    link.href = `#player-${player.uid}`;
    link.textContent = player.label;
    nav.appendChild(link);
  });
}

function createSection(player) {
  const section = document.createElement("section");
  section.className = "section";
  section.id = `player-${player.uid}`;

  section.innerHTML = `
    <div class="section__header">
      <div>
        <h2 class="section__title">${player.label}</h2>
        <p class="section__meta">UID: <code>${player.uid}</code> — ${player.description}</p>
      </div>
      <div class="badge" id="badge-${player.uid}">Loading data…</div>
    </div>
    <div class="cards" id="cards-${player.uid}"></div>
    <div class="chart-wrapper">
      <div id="chart-${player.uid}" class="chart"></div>
    </div>
    <h3>Likes Activity</h3>
    <div class="table-wrapper">
      <table class="table" id="likes-table-${player.uid}">
        <thead>
          <tr>
            <th>Date</th>
            <th>Before</th>
            <th>After</th>
            <th>Received</th>
            <th>Success</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  `;

  return section;
}

function populateCards(uid, summaryRow) {
  const container = document.getElementById(`cards-${uid}`);
  container.innerHTML = "";
  if (!summaryRow) return;

  const avgDaily = Number(summaryRow["Average Daily XP Gained"]);
  const cards = [
    { label: "Days Logged", value: formatNumber(summaryRow["Days Logged"]) },
    { label: "Start XP", value: formatNumber(summaryRow["Start XP"]) },
    { label: "End XP", value: formatNumber(summaryRow["End XP"]) },
    { label: "Total XP Gain", value: formatNumber(summaryRow["Total XP Gained"]) },
    { label: "Avg Daily XP", value: Number.isFinite(avgDaily) ? avgDaily.toFixed(2) : formatNumber(summaryRow["Average Daily XP Gained"]) },
  ];

  cards.forEach((card) => {
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `
      <div class="card__label">${card.label}</div>
      <div class="card__value">${card.value}</div>
    `;
    container.appendChild(div);
  });
}

function populateLikesTable(uid, likesRows) {
  const tbody = document.querySelector(`#likes-table-${uid} tbody`);
  tbody.innerHTML = "";

  likesRows.slice(-10).reverse().forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.Date || "-"}</td>
      <td>${formatNumber(row["Likes Before"])}</td>
      <td>${formatNumber(row["Likes After"])}</td>
      <td>${formatNumber(row["Likes Received"])}</td>
      <td>${(row.Success || "").toString().toUpperCase()}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderChart(uid, series, monthLabel) {
  const target = document.getElementById(`chart-${uid}`);
  if (!series.length) {
    target.innerHTML = "<p>No daily data available for the latest month.</p>";
    return;
  }

  const options = {
    chart: {
      type: "area",
      height: 320,
      toolbar: { show: false },
      fontFamily: "Inter, sans-serif",
      foreColor: "#e2e8f0",
    },
    stroke: {
      width: 2,
      curve: "smooth",
    },
    dataLabels: { enabled: false },
    fill: {
      type: "gradient",
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.45,
        opacityTo: 0.05,
        stops: [0, 90, 100],
      },
    },
    colors: ["#38bdf8"],
    series: [
      {
        name: "XP",
        data: series.map((point) => ({ x: point.date, y: point.xp })),
      },
    ],
    xaxis: {
      type: "category",
      labels: {
        style: { colors: "#94a3b8" },
      },
    },
    yaxis: {
      labels: {
        formatter: (value) => Number(value).toLocaleString(),
        style: { colors: "#94a3b8" },
      },
    },
    tooltip: {
      theme: "dark",
      y: {
        formatter: (value) => Number(value).toLocaleString(),
      },
    },
    title: {
      text: `Daily XP for ${monthLabel}`,
      style: { fontSize: "16px", color: "#e2e8f0" },
    },
  };

  const chart = new ApexCharts(target, options);
  chart.render();
}

async function loadPlayer(uid) {
  const summary = await loadCsv(`${REMOTE_BASE}/players/${uid}/summary.csv`);
  const likes = await loadCsv(`${REMOTE_BASE}/players/${uid}/likes_activity.csv`).catch(() => []);

  const latest = getLatestMonth(summary);
  let dailySeries = [];
  let monthLabel = "";

  if (latest) {
    const monthlyFile = encodeURIComponent(`${latest.year} ${latest.monthNumber}.CSV`);
    try {
      const monthly = await loadCsv(`${REMOTE_BASE}/players/${uid}/${monthlyFile}`);
      dailySeries = monthly
        .filter((row) => row.Date && row.XP)
        .map((row) => ({
          date: row.Date,
          xp: Number(row.XP),
        }));
      monthLabel = `${latest.monthName} ${latest.year}`;
    } catch (err) {
      console.warn(`Could not load monthly file for ${uid}:`, err);
    }
  }

  const fallbackRow = summary.find((row) => row.Month === "ALL") || summary[summary.length - 1] || null;
  const latestSummaryRow = latest
    ? summary.find((row) => row.Month === latest.monthName && row.Year === latest.year) || fallbackRow
    : fallbackRow;

  return {
    summary,
    likes,
    dailySeries,
    monthLabel,
    latestSummaryRow,
  };
}\n\nfunction setBadge(uid, text) {
  const badge = document.getElementById(`badge-${uid}`);
  if (badge) badge.textContent = text;
}

async function init() {
  renderNav(PLAYERS);
  const container = document.getElementById("player-sections");

  PLAYERS.forEach((player) => {
    const section = createSection(player);
    container.appendChild(section);
  });

  for (const player of PLAYERS) {
    try {
      const data = await loadPlayer(player.uid);
      const summaryRow = data.latestSummaryRow || data.summary.find((row) => row.Month === "ALL") || data.summary[data.summary.length - 1];
      populateCards(player.uid, summaryRow);
      populateLikesTable(player.uid, data.likes);
      renderChart(player.uid, data.dailySeries, data.monthLabel || "latest month");
      setBadge(player.uid, `Latest month: ${data.monthLabel || "N/A"}`);
    } catch (error) {
      console.error(`Failed to render player ${player.uid}:`, error);
      setBadge(player.uid, "Data unavailable");
    }
  }
}

document.addEventListener("DOMContentLoaded", init);






