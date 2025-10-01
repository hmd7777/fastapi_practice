// ===== Config =====
const API_BASE = "http://127.0.0.1:8000";

// ===== DOM =====
const elYearly = document.getElementById("chart-yearly");
const elOpp    = document.getElementById("chart-opponents");
const elGoals  = document.getElementById("chart-goals");
const elRace   = document.getElementById("chart-race");

const chartYearly = echarts.init(elYearly);
const chartOpp    = echarts.init(elOpp);
const chartGoals  = echarts.init(elGoals || document.createElement("div"));
const chartRace   = echarts.init(elRace);
[new ResizeObserver(()=>chartYearly.resize()).observe(elYearly),
 new ResizeObserver(()=>chartOpp.resize()).observe(elOpp),
 elGoals && new ResizeObserver(()=>chartGoals.resize()).observe(elGoals),
 new ResizeObserver(()=>chartRace.resize()).observe(elRace)];

const chartSelect      = document.getElementById("chartSelect");
const teamInput        = document.getElementById("teamInput");
const loadBtn          = document.getElementById("loadBtn");
const tournamentSelect = document.getElementById("tournamentSelect");
const yearFromInput    = document.getElementById("yearFrom");
const yearToInput      = document.getElementById("yearTo");

// ===== Helpers (URLs, filters, UI) =====
function teamOrDefault() {
  return (teamInput.value || "").trim() || "England";
}

function getFilterParams() {
  const p = {};
  const t = (tournamentSelect?.value || "").trim();
  if (t) p.tournament = t;

  const yf = parseInt(yearFromInput?.value ?? "", 10);
  const yt = parseInt(yearToInput?.value ?? "", 10);
  if (!Number.isNaN(yf) && !Number.isNaN(yt)) {
    const from = Math.min(yf, yt);
    const to   = Math.max(yf, yt);
    p.date_from = `${from}-01-01`;
    p.date_to   = `${to}-12-31`;
  }
  return p;
}

function apiUrl(path, params = {}) {
  const merged = { ...getFilterParams(), ...params };
  const qs = new URLSearchParams();
  Object.entries(merged).forEach(([k,v]) => {
    if (v !== undefined && v !== null && String(v).length) qs.append(k, v);
  });
  return `${API_BASE}${path}${qs.toString() ? `?${qs.toString()}` : ""}`;
}

async function fetchJSON(path, params) {
  const res = await fetch(apiUrl(path, params));
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function showOnly(targetEl) {
  [elYearly, elOpp, elGoals, elRace].forEach(el => {
    if (!el) return;
    el.classList.toggle("hidden", el !== targetEl);
  });
}

// ===== Data loaders =====
async function loadYearly(team) {
  chartYearly.showLoading();
  try {
    const data = await fetchJSON("/stats/yearly", { team });
    const rows = (data.items || []).sort((a,b) => a.year - b.year);
    if (!rows.length) {
      chartYearly.setOption({ title: { text: `No data for "${team}"` }, series: [] });
      return;
    }
    chartYearly.setOption({
      title: { text: `${team} — Wins / Draws / Losses per Year` },
      tooltip: { trigger: "axis" },
      legend: {},
      dataZoom: [{ type: "inside" }, {}],
      xAxis: { type: "category" },
      yAxis: { type: "value" },
      dataset: {
        source: [
          ["year","wins","draws","losses"],
          ...rows.map(r => [String(r.year), r.wins, r.draws, r.losses])
        ]
      },
      series: [
        { name: "Wins",   type: "line", areaStyle: {}, stack: "total", encode: { x: "year", y: "wins" } },
        { name: "Draws",  type: "line", areaStyle: {}, stack: "total", encode: { x: "year", y: "draws" } },
        { name: "Losses", type: "line", areaStyle: {}, stack: "total", encode: { x: "year", y: "losses" } },
      ]
    });
  } catch (e) {
    console.error(e);
    chartYearly.setOption({ title: { text: "Failed to load yearly stats" }, series: [] });
  } finally {
    chartYearly.hideLoading();
  }
}

async function loadOpponents(team) {
  chartOpp.showLoading();
  try {
    const data = await fetchJSON("/stats/opponents", { team, top: 15 });
    const rows = data.items || [];
    if (!rows.length) {
      chartOpp.setOption({ title: { text: `No opponents for "${team}"` }, series: [] });
      return;
    }
    chartOpp.setOption({
      title: { text: `${team} — Top Opponents by Matches` },
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      grid: { left: 120, right: 16, top: 40, bottom: 20 },
      xAxis: { type: "value", name: "Matches" },
      yAxis: { type: "category", data: rows.map(r => r.opponent), inverse: true },
      series: [{
        type: "bar",
        data: rows.map(r => r.played),
        label: {
          show: true, position: "right",
          formatter: p => {
            const r = rows[p.dataIndex];
            const wr = Math.round((r.win_rate || 0) * 100);
            return `${p.value}  (W${r.wins}/D${r.draws}/L${r.losses}, ${wr}%)`;
          }
        }
      }]
    });
  } catch (e) {
    console.error(e);
    chartOpp.setOption({ title: { text: "Failed to load opponents" }, series: [] });
  } finally {
    chartOpp.hideLoading();
  }
}

async function loadGoalsTrend(team) {
  if (!elGoals) return;
  chartGoals.showLoading();
  try {
    const data = await fetchJSON("/stats/yearly", { team });
    const rows = (data.items || []).sort((a,b) => a.year - b.year);
    if (!rows.length) {
      chartGoals.setOption({ title: { text: `No data for "${team}"` }, series: [] });
      return;
    }
    chartGoals.setOption({
      title: { text: `${team} — Goals For vs Against per Year` },
      tooltip: { trigger: "axis" },
      legend: {},
      dataZoom: [{ type: "inside" }, {}],
      xAxis: { type: "category", data: rows.map(r => String(r.year)) },
      yAxis: { type: "value", name: "Goals" },
      series: [
        { name: "Goals For",     type: "line", areaStyle: {}, data: rows.map(r => r.gf) },
        { name: "Goals Against", type: "line", areaStyle: {}, data: rows.map(r => r.ga) }
      ]
    });
  } catch (e) {
    console.error(e);
    chartGoals.setOption({ title: { text: "Failed to load goals trend" }, series: [] });
  } finally {
    chartGoals.hideLoading();
  }
}

// ===== Bar race (per-year or cumulative) =====
let raceTimer = null;
function stopRace(){ if (raceTimer) { clearInterval(raceTimer); raceTimer = null; } }

// endpoint: "top_by_year" or "top_cumulative"; metric: "wins"|"gf"
async function renderRace(endpoint, metric = "wins", topN = 10, speedMs = 1200) {
  stopRace();
  chartRace.showLoading();

  try {
    const data = await fetchJSON(`/stats/${endpoint}`, { metric, top: topN });
    const items = data.items || [];
    if (!items.length) {
      chartRace.setOption({ title: { text: "No data" }, series: [] });
      return;
    }

    let idx = 0;
    function paint(year, topRows) {
      const rows = [...topRows].sort((a,b) => b[metric] - a[metric]);
      const names = rows.map(r => r.team);
      const values = rows.map(r => r[metric]);

      chartRace.setOption({
        title: { text: `Top ${topN} — ${endpoint === "top_cumulative" ? "Cumulative" : "Per year"} by ${metric.toUpperCase()} — ${year}` },
        grid: { top: 20, bottom: 40, left: 150, right: 40 },
        xAxis: { max: 'dataMax' },
        yAxis: { type: 'category', inverse: true, data: names, max: topN },
        series: [{
          type: 'bar',
          realtimeSort: true,
          data: values,
          label: { show: true, position: 'right', valueAnimation: true }
        }],
        animationDuration: 0,
        animationDurationUpdate: 700,
        animationEasing: 'linear',
        animationEasingUpdate: 'linear'
      });
    }

    paint(items[0].year, items[0].top);
    chartRace.hideLoading();

    raceTimer = setInterval(() => {
      idx = (idx + 1) % items.length;
      const it = items[idx];
      paint(it.year, it.top);
    }, speedMs);
  } catch (e) {
    console.error(e);
    chartRace.setOption({ title: { text: "Failed to load bar race" }, series: [] });
  } finally {
    chartRace.hideLoading();
  }
}

// ===== Selector routing =====
async function renderSelected(team) {
  const type = chartSelect.value;
  stopRace();

  if (type === "yearly") {
    showOnly(elYearly);
    await loadYearly(team);
  } else if (type === "opponents") {
    showOnly(elOpp);
    await loadOpponents(team);
  } else if (type === "goals_trend") {
    showOnly(elGoals);
    await loadGoalsTrend(team);
  } else if (type === "race_yearly_wins") {
    showOnly(elRace);
    await renderRace("top_by_year", "wins", 10);
  } else if (type === "race_yearly_goals") {
    showOnly(elRace);
    await renderRace("top_by_year", "gf", 10);
  } else if (type === "race_cum_wins") {
    showOnly(elRace);
    await renderRace("top_cumulative", "wins", 10);
  } else if (type === "race_cum_goals") {
    showOnly(elRace);
    await renderRace("top_cumulative", "gf", 10);
  }
}

// ===== Populate tournaments, defaults, and listeners =====
async function populateTournaments() {
  try {
    const list = await fetchJSON("/meta/tournaments");
    for (const t of list) {
      const opt = document.createElement("option");
      opt.value = t.name;
      opt.textContent = `${t.name} (${t.matches})`;
      tournamentSelect.appendChild(opt);
    }
  } catch (e) {
    console.warn("Failed to load tournaments", e);
  }
}

// defaults
teamInput.value     = "England";
yearFromInput.value = "1872";
yearToInput.value   = "2017";
populateTournaments();

// events
loadBtn.addEventListener("click", () => renderSelected(teamOrDefault()));
teamInput.addEventListener("keydown", e => e.key === "Enter" && renderSelected(teamOrDefault()));
chartSelect.addEventListener("change", () => renderSelected(teamOrDefault()));
tournamentSelect.addEventListener("change", () => renderSelected(teamOrDefault()));
yearFromInput.addEventListener("change", () => renderSelected(teamOrDefault()));
yearToInput.addEventListener("change", () => renderSelected(teamOrDefault()));

// initial paint
renderSelected(teamOrDefault());
