let chartInstance = null;

const METHOD_LABELS = {
  moreira_2025: "Moreira 2025",
  v_percent: "V%",
  al_ca_mg: "Al+Ca+Mg",
  smp: "SMP",
};

const METHOD_COLORS = {
  moreira_2025: "#15803d",
  v_percent: "#d97706",
  al_ca_mg: "#d97706",
  smp: "#d97706",
};

export function renderChart(results, primaryMethod) {
  const canvas = document.getElementById("comparison-chart");
  const fallback = document.getElementById("chart-fallback");

  if (typeof Chart === "undefined") {
    canvas.style.display = "none";
    fallback.style.display = "block";
    fallback.innerHTML = renderFallbackBars(results, primaryMethod);
    return;
  }

  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  const available = results.filter(r => r.available);
  const labels = available.map(r => METHOD_LABELS[r.method] || r.method);
  const values = available.map(r => r.nc_tha);
  const colors = available.map(r =>
    r.method === "moreira_2025" ? METHOD_COLORS.moreira_2025
    : r.method === primaryMethod ? METHOD_COLORS[r.method] || "#d97706"
    : "#94a3b8"
  );

  chartInstance = new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "NC (t/ha)",
        data: values,
        backgroundColor: colors,
        borderRadius: 6,
        barThickness: 48,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => `${ctx.parsed.y.toFixed(2)} t/ha`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: "NC (t/ha)", font: { family: "'DM Sans', sans-serif" } },
          ticks: { font: { family: "'JetBrains Mono', monospace" } },
        },
        x: {
          ticks: { font: { family: "'DM Sans', sans-serif", weight: "600" } },
        },
      },
    },
  });
}

function renderFallbackBars(results, primaryMethod) {
  const available = results.filter(r => r.available);
  if (available.length === 0) return "";
  const max = Math.max(...available.map(r => r.nc_tha), 1);
  return `<div style="display:flex;align-items:flex-end;gap:1rem;height:200px;padding:1rem 0;">
    ${available.map(r => {
      const pct = Math.round((r.nc_tha / max) * 100);
      const color = r.method === "moreira_2025" ? "#15803d" : r.method === primaryMethod ? "#d97706" : "#94a3b8";
      const label = METHOD_LABELS[r.method] || r.method;
      return `<div style="flex:1;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;">
        <span style="font-family:var(--font-mono);font-size:0.85rem;font-weight:600;margin-bottom:0.25rem;">${r.nc_tha.toFixed(2)}</span>
        <div style="width:100%;max-width:60px;height:${pct}%;background:${color};border-radius:6px 6px 0 0;"></div>
        <span style="font-size:0.8rem;font-weight:600;margin-top:0.5rem;">${label}</span>
      </div>`;
    }).join("")}
  </div>`;
}

export function destroyChart() {
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
}
