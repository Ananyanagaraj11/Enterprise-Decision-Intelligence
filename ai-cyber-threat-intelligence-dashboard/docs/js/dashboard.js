/* ============================================
   SOC Lite – AI IDS Dashboard Controller
   Full Final Version – Dark Neon Themed
   ============================================ */

/* Same origin when served from backend (port 8000), else ENV for Render */
const API_BASE = (typeof window !== "undefined" && window.ENV_API_BASE != null && window.ENV_API_BASE !== "")
    ? window.ENV_API_BASE
    : (window.location.port === "8000" ? "" : window.location.origin);

let predictionHistory = [];
let totalPredictions = 0;
let attackCount = 0;
let lastClassDistribution = null;
let lastConfidenceBuckets = null;

/* ============================================
   INIT
   ============================================ */

document.addEventListener("DOMContentLoaded", async () => {
    updateClock();
    setInterval(updateClock, 1000);

    initializeCharts();
    await loadLatestAnalysis();

    const runBtn = document.getElementById("runPredictionBtn");
    if (runBtn) runBtn.addEventListener("click", runLivePrediction);
});

/* ============================================
   RUN LIVE PREDICTION (single sample)
   ============================================ */

async function runLivePrediction() {
    var runBtn = document.getElementById("runPredictionBtn");
    if (runBtn) runBtn.disabled = true;
    try {
        var configRes = await fetch(API_BASE + "/config", { cache: "no-store" });
        if (!configRes.ok) throw new Error("Config failed");
        var config = await configRes.json();
        var dim = config.input_dim || 78;
        var features = Array(dim).fill(0).map(() => Math.random() * 2 - 1);

        var predRes = await fetch(API_BASE + "/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ features: features })
        });
        if (!predRes.ok) throw new Error("Predict failed");
        var pred = await predRes.json();

        predictionHistory.push({
            index: predictionHistory.length,
            predicted_class: pred.predicted_class,
            confidence: pred.confidence,
            actual_label: null
        });
        totalPredictions = predictionHistory.length;
        attackCount = predictionHistory.filter(p => p.predicted_class !== "BENIGN").length;
        lastClassDistribution = null;
        lastConfidenceBuckets = null;

        updateKPIs();
        updateCharts();
        populateAlerts();
        populateTable();
        var csvSection = document.getElementById("csvResultsSection");
        if (csvSection) csvSection.style.display = "block";
    } catch (e) {
        console.error(e);
        alert("Backend not reachable. Start the server on port 8000.");
    }
    if (runBtn) runBtn.disabled = false;
}

/* ============================================
   CLOCK
   ============================================ */

function updateClock() {
    const el = document.getElementById("clock");
    if (el && typeof moment !== "undefined") {
        el.textContent = moment().format("MMM DD, YYYY | HH:mm:ss");
    }
}

/* ============================================
   LOAD BACKEND ANALYSIS
   ============================================ */

async function loadLatestAnalysis() {
    try {
        const response = await fetch(`${API_BASE}/api/last-analysis`, {
            cache: "no-store"
        });

        if (response.ok) {
            const data = await response.json();
            if (data && (data.total_rows > 0 || (data.predictions && data.predictions.length > 0))) {
                applyAnalysis(data);
                console.log("Dashboard loaded fresh backend analysis");
            }
        }
    } catch (err) {
        console.error("Backend not reachable:", err);
    }
}

/* ============================================
   APPLY DATA
   ============================================ */

function applyAnalysis(data) {
    /* Backend sends first 100 in predictions; full counts in summary */
    predictionHistory = data.predictions || [];
    totalPredictions = data.total_rows ?? predictionHistory.length;

    attackCount =
        data.summary?.total_attacks ??
        predictionHistory.filter(p => p.predicted_class !== "BENIGN").length;

    lastClassDistribution = data.summary?.class_distribution ?? null;
    lastConfidenceBuckets = data.summary?.confidence_buckets ?? null;

    updateKPIs();
    updateCharts();
    populateAlerts();
    populateTable();

    var csvSection = document.getElementById("csvResultsSection");
    if (csvSection && (predictionHistory.length > 0 || totalPredictions > 0))
        csvSection.style.display = "block";
}

/* ============================================
   KPI UPDATE
   ============================================ */

function updateKPIs() {
    var el;
    if ((el = document.getElementById("totalEvents"))) el.textContent = totalPredictions;
    if ((el = document.getElementById("attackEvents"))) el.textContent = attackCount;
    const percent =
        totalPredictions > 0
            ? ((attackCount / totalPredictions) * 100).toFixed(1)
            : 0;
    if ((el = document.getElementById("attackPercent"))) el.textContent = percent;
}

/* ============================================
   CHART INITIALIZATION
   ============================================ */

function initializeCharts() {

    const layoutBase = {
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: "#e0f2fe" },
        margin: { l: 44, r: 16, t: 24, b: 36 },
        autosize: true
    };

    Plotly.newPlot("attackDistPie", [{
        values: [1],
        labels: ["No Data"],
        type: "pie",
        hole: 0.5,
        marker: { colors: ["#f8fafc"] }
    }], layoutBase);

    Plotly.newPlot("topAttacksBar", [{
        x: [0],
        y: ["No Data"],
        type: "bar",
        orientation: "h",
        marker: { color: "#f8fafc" }
    }], layoutBase);

    Plotly.newPlot("severityLine", [{
        x: [],
        y: [],
        type: "scatter",
        mode: "lines",
        fill: "tozeroy",
        line: { color: "#b91c1c", width: 3 }
    }], layoutBase);

    Plotly.newPlot("eventsTimeline", [], layoutBase);

    var layoutConf = { ...layoutBase };
    Plotly.newPlot("confidenceDist", [{
        x: ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"],
        y: [0, 0, 0, 0, 0],
        type: "bar",
        marker: { color: "#f8fafc" }
    }], layoutConf);
}

/* ============================================
   UPDATE CHARTS
   ============================================ */

var chartLayoutUpdate = {
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: "#e0f2fe" },
    margin: { l: 44, r: 16, t: 24, b: 36 },
    autosize: true
};

function updateCharts() {
    updatePie();
    updateBar();
    updateSeverity();
    updateTimeline();
    updateConfidenceDist();
}

/* ---------- PIE ---------- */

function updatePie() {
    const counts = {};

    if (lastClassDistribution) {
        Object.assign(counts, lastClassDistribution);
    } else {
        predictionHistory.forEach(p => {
            counts[p.predicted_class] =
                (counts[p.predicted_class] || 0) + 1;
        });
    }

    const labels = Object.keys(counts);
    const values = Object.values(counts);
    if (labels.length === 0) { labels.push("No Data"); values.push(1); }

    const chartColors = [
        "#f8fafc",  /* BENIGN – white */
        "#dc2626",  /* attack – red */
        "#ea580c",  /* attack – orange */
        "#ca8a04",  /* attack – amber */
        "#16a34a",  /* green */
        "#2563eb",  /* blue */
        "#9333ea"   /* purple */
    ];

    Plotly.react("attackDistPie", [{
        values,
        labels,
        type: "pie",
        hole: 0.5,
        marker: { colors: chartColors },
        textinfo: "percent",
        textposition: "inside"
    }], chartLayoutUpdate);
}

/* ---------- BAR ---------- */

function updateBar() {
    const counts = {};

    if (lastClassDistribution) {
        Object.assign(counts, lastClassDistribution);
    } else {
        predictionHistory.forEach(p => {
            counts[p.predicted_class] =
                (counts[p.predicted_class] || 0) + 1;
        });
    }

    const sorted = Object.entries(counts)
        .sort((a, b) => b[1] - a[1]);
    if (sorted.length === 0) sorted.push(["No Data", 0]);

    const attackColors = ["#dc2626", "#ea580c", "#ca8a04", "#16a34a", "#2563eb", "#9333ea"];
    const yLabels = sorted.map(s => s[0]);
    let attackIdx = 0;
    const colors = yLabels.map(function (label) {
        if (label === "BENIGN") return "#f8fafc";
        return attackColors[attackIdx++ % attackColors.length];
    });

    Plotly.react("topAttacksBar", [{
        x: sorted.map(s => s[1]),
        y: yLabels,
        type: "bar",
        orientation: "h",
        marker: { color: colors }
    }], chartLayoutUpdate);
}

/* ---------- CONFIDENCE DISTRIBUTION ---------- */

function updateConfidenceDist() {
    var labels = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"];
    var buckets;
    if (lastConfidenceBuckets && Array.isArray(lastConfidenceBuckets) && lastConfidenceBuckets.length === 5) {
        buckets = lastConfidenceBuckets.slice();
    } else {
        buckets = [0, 0, 0, 0, 0];
        predictionHistory.forEach(function (p) {
            var pct = Math.round((p.confidence || 0) * 100);
            pct = Math.max(0, Math.min(100, pct));
            var idx = pct <= 20 ? 0 : pct <= 40 ? 1 : pct <= 60 ? 2 : pct <= 80 ? 3 : 4;
            buckets[idx]++;
        });
    }
    var total = buckets.reduce(function (a, b) { return a + b; }, 0);
    var layout = Object.assign({}, chartLayoutUpdate);
    layout.xaxis = { type: "category", categoryorder: "array", categoryarray: labels, tickangle: 0 };
    layout.yaxis = layout.yaxis || {};
    if (total === 0) {
        layout.yaxis.range = [0, 1];
        layout.annotations = [{ x: 2, y: 0.5, text: "No data", showarrow: false, font: { size: 14 }, xref: "x", yref: "paper" }];
        Plotly.react("confidenceDist", [{
            x: labels,
            y: [0, 0, 0, 0, 0],
            type: "bar",
            orientation: "v",
            marker: { color: "#f8fafc" },
            hovertemplate: "%{x}: 0<extra></extra>"
        }], layout);
        return;
    }
    var pctValues = buckets.map(function (c) { return total > 0 ? (c / total * 100) : 0; });
    layout.yaxis.range = [0, 100];
    layout.yaxis.ticksuffix = "%";
    Plotly.react("confidenceDist", [{
        x: labels,
        y: pctValues,
        type: "bar",
        orientation: "v",
        marker: { color: "#f8fafc" },
        text: buckets.map(function (c) { return c.toLocaleString(); }),
        textposition: "outside",
        hovertemplate: "%{x}<br>Count: %{text}<br>Share: %{y:.1f}%<extra></extra>"
    }], layout);
}

/* ---------- SEVERITY LINE ---------- */

function updateSeverity() {
    const severityScores = predictionHistory.map(p =>
        p.predicted_class !== "BENIGN" ? p.confidence : 0
    );
    if (severityScores.length === 0) severityScores.push(0);

    Plotly.react("severityLine", [{
        x: severityScores.map((_, i) => i + 1),
        y: severityScores,
        type: "scatter",
        mode: "lines",
        fill: "tozeroy",
        line: { color: "#b91c1c", width: 2 }
    }], chartLayoutUpdate);
}

/* ---------- TIMELINE ---------- */

function updateTimeline() {
    let total = 0;
    let attacks = 0;
    let benign = 0;

    const totalArr = [];
    const attackArr = [];
    const benignArr = [];

    predictionHistory.forEach(p => {
        total++;
        if (p.predicted_class === "BENIGN") benign++;
        else attacks++;

        totalArr.push(total);
        attackArr.push(attacks);
        benignArr.push(benign);
    });
    if (totalArr.length === 0) { totalArr.push(1); attackArr.push(0); benignArr.push(0); }

    Plotly.react("eventsTimeline", [
        {
            x: totalArr.map((_, i) => i + 1),
            y: totalArr,
            type: "scatter",
            mode: "lines",
            name: "Total",
            line: { color: "#f8fafc" }
        },
        {
            x: totalArr.map((_, i) => i + 1),
            y: attackArr,
            type: "scatter",
            mode: "lines",
            name: "Attacks",
            line: { color: "#b91c1c" }
        },
        {
            x: totalArr.map((_, i) => i + 1),
            y: benignArr,
            type: "scatter",
            mode: "lines",
            name: "Benign",
            line: { color: "#15803d" }
        }
    ], chartLayoutUpdate);
}

/* ============================================
   ALERTS
   ============================================ */

function populateAlerts() {
    const container = document.getElementById("alertsTable");
    if (!container) return;

    container.innerHTML = "";

    predictionHistory.slice(-10).reverse().forEach(pred => {
        const div = document.createElement("div");
        div.className = "alert-item";
        div.innerHTML = `
            <div><strong>${pred.predicted_class}</strong></div>
            <div>Confidence: ${(pred.confidence * 100).toFixed(1)}%</div>
        `;
        container.appendChild(div);
    });
}

/* ============================================
   TABLE
   ============================================ */

function populateTable() {
    const tbody = document.getElementById("csvResultsTableBody");
    if (!tbody) return;

    tbody.innerHTML = "";

    predictionHistory.slice(0, 1000).forEach((pred, i) => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${i + 1}</td>
            <td>${pred.predicted_class}</td>
            <td>${(pred.confidence * 100).toFixed(1)}%</td>
            <td>${pred.actual_label || "N/A"}</td>
            <td>${pred.actual_label
                ? (pred.actual_label === pred.predicted_class ? "✓" : "✗")
                : "N/A"}
            </td>
        `;

        tbody.appendChild(row);
    });
}