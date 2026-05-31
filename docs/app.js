// Carga resumen.json (generado por scripts/02_analysis.py) y dibuja los graficos.
const fmtUSD = (n) => "$" + Math.round(n).toLocaleString("es-EC");
const fmtPct = (n) => n.toLocaleString("es-EC") + "%";
const fmtNum = (n) => Math.round(n).toLocaleString("es-EC");

// Paleta consistente con styles.css
const C = { ink: "#e7edf3", muted: "#93a1b0", hl: "#ffd166", accent: "#06d6a0", line: "#2a3441" };

Chart.defaults.color = C.muted;
Chart.defaults.borderColor = C.line;
Chart.defaults.font.family = "-apple-system, Segoe UI, Roboto, sans-serif";

const Q_LABELS = ["Q1\n(más pobre)", "Q2", "Q3", "Q4", "Q5\n(más rico)"];
const Q_COLORS = ["#ef476f", "#f78c6b", C.hl, "#83d483", C.accent];

fetch("data/resumen.json")
  .then((r) => r.json())
  .then(render)
  .catch((e) => {
    document.querySelector("main").insertAdjacentHTML(
      "afterbegin",
      `<div class="card"><h2>No se pudo cargar resumen.json</h2><p>Corre <code>python3 scripts/02_analysis.py</code> para generarlo.</p></div>`
    );
    console.error(e);
  });

function render(d) {
  const h = d.hogar, ind = d.ingreso_individual, a = d.ayuda_otros_hogares;
  const pp = d.quintiles.por_persona, ppg = pp.grupos, q5 = ppg[4];

  // --- Mensaje central ---
  text("t-bajo", fmtPct(h.pct_bajo_media));
  text("t-media", fmtUSD(h.media));
  text("t-sintop", fmtUSD(h.media_sin_top10));
  text("t-mediana", fmtUSD(h.mediana));

  // --- Bloque 1: la media engaña (solo tarjetas) ---
  text("pct-media", fmtPct(h.pct_alcanza_media));
  text("s-media", fmtUSD(h.media));
  text("s-mediana", fmtUSD(h.mediana));
  text("s-p90", fmtUSD(h.p90));

  // --- Bloque 2: concentracion del ingreso (% nacional por quintil de personas) ---
  text("q5pc-share", fmtPct(q5.pct_ingreso_nacional));
  text("ratio-pc", pp.ratio_q5_q1.toLocaleString("es-EC"));
  new Chart(document.getElementById("chartShare"), {
    type: "bar",
    data: {
      labels: Q_LABELS,
      datasets: [{
        label: "% del ingreso nacional",
        data: ppg.map((g) => g.pct_ingreso_nacional),
        backgroundColor: Q_COLORS,
        borderRadius: 6,
      }],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => fmtPct(c.parsed.y) + " del ingreso nacional" } },
      },
      scales: { y: { ticks: { callback: (v) => v + "%" } } },
    },
  });

  // --- Bloque 3: ingreso vs gasto per capita por quintil ---
  text("q1pc-ing", fmtUSD(ppg[0].ingreso_per_capita));
  text("q5pc-ing", fmtUSD(q5.ingreso_per_capita));
  text("q5pc-ahorro", fmtPct(q5.tasa_ahorro_pct));
  new Chart(document.getElementById("chartPcIng"), {
    type: "bar",
    data: {
      labels: Q_LABELS,
      datasets: [
        { label: "Ingreso per cápita", data: ppg.map((g) => g.ingreso_per_capita), backgroundColor: C.accent, borderRadius: 5 },
        { label: "Gasto per cápita", data: ppg.map((g) => g.gasto_per_capita), backgroundColor: "#ef476f", borderRadius: 5 },
      ],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top" },
        tooltip: {
          callbacks: {
            label: (c) => c.dataset.label + ": " + fmtUSD(c.parsed.y),
            afterBody: (items) => {
              const g = ppg[items[0].dataIndex];
              const signo = g.tasa_ahorro_pct < 0 ? "Desahorro: " : "Ahorro: ";
              return signo + fmtPct(g.tasa_ahorro_pct);
            },
          },
        },
      },
      scales: { y: { ticks: { callback: (v) => fmtUSD(v) } } },
    },
  });

  // --- Bloque 4: perceptores por hogar (dona) ---
  text("prom-perc", d.perceptores.promedio_por_hogar);
  const dist = d.perceptores.distribucion_pct;
  const orden = ["0", "1", "2", "3", "4+"].filter((k) => k in dist);
  new Chart(document.getElementById("chartPerc"), {
    type: "doughnut",
    data: {
      labels: orden.map((k) => `${k} perceptor${k === "1" ? "" : "es"}`),
      datasets: [{
        data: orden.map((k) => dist[k]),
        backgroundColor: ["#3a4654", C.accent, C.hl, "#ef476f", "#7c5cff"],
        borderColor: C.card,
        borderWidth: 2,
      }],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right" },
        tooltip: { callbacks: { label: (c) => `${c.label}: ${fmtPct(c.parsed)}` } },
      },
    },
  });

  // --- Bloque 5: % que gana al menos cada umbral ---
  text("ind-mediana", fmtUSD(ind.mediana));
  const u1200 = ind.umbrales.find((x) => x.umbral === 1200);
  text("ind-1200", fmtNum(u1200.personas));
  text("ind-1200-pct", fmtPct(u1200.pct));
  new Chart(document.getElementById("chartUmbral"), {
    type: "bar",
    data: {
      labels: ind.umbrales.map((u) => "≥ " + fmtUSD(u.umbral)),
      datasets: [{
        label: "% de perceptores",
        data: ind.umbrales.map((u) => u.pct),
        backgroundColor: ind.umbrales.map((u) => (u.umbral === 1200 ? C.hl : C.accent)),
        borderRadius: 6,
      }],
    },
    options: {
      indexAxis: "y",
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (c) => {
              const u = ind.umbrales[c.dataIndex];
              return `${fmtPct(u.pct)} — ${fmtNum(u.personas)} personas`;
            },
          },
        },
      },
      scales: { x: { ticks: { callback: (v) => v + "%" }, max: 100 } },
    },
  });

  // --- Bloque 6: ayuda a otros hogares ---
  text("ayuda-total", fmtUSD(a.total_mensual_usd));
  text("a-total", fmtUSD(a.total_mensual_usd));
  text("a-pct", fmtPct(a.pct_hogares_que_dan));
  text("a-prom", fmtUSD(a.promedio_entre_quienes_dan));

  // --- meta ---
  text("meta-muestra", `${fmtNum(d.meta.muestra_viviendas)} viviendas encuestadas`);
  const repo = document.getElementById("repo-link");
  if (repo) repo.href = "https://github.com/LuisReinoso/enighur-2025-analisis";
}

function text(id, v) {
  const el = document.getElementById(id);
  if (el) el.textContent = v;
}
