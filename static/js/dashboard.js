(() => {
  let lastReport = null;
  let complexityChart = null;
  let gateChart = null;

  // ---------- view switching ----------
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach((btn) => {
    btn.addEventListener("click", () => {
      navItems.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
      document.getElementById(`view-${btn.dataset.view}`).classList.remove("hidden");
    });
  });

  // ---------- upload status helper ----------
  function setStatus(msg, kind) {
    const el = document.getElementById("upload-status");
    el.textContent = msg;
    el.className = "upload-status" + (kind ? " " + kind : "");
  }

  // ---------- fetch helpers ----------
  async function runAnalyze(formData) {
    setStatus("Analyzing...", "");
    try {
      const resp = await fetch("/api/analyze", { method: "POST", body: formData });
      const data = await resp.json();
      if (!resp.ok) {
        setStatus(data.error || "Analysis failed", "err");
        return;
      }
      setStatus(
        `Analyzed ${data.meta.files_parsed}/${data.meta.total_files_submitted} files in ${data.meta.analysis_seconds}s`,
        "ok"
      );
      renderReport(data);
    } catch (err) {
      setStatus("Network error: " + err.message, "err");
    }
  }

  async function runSample() {
    setStatus("Running sample analysis...", "");
    try {
      const resp = await fetch("/api/sample");
      const data = await resp.json();
      setStatus(`Sample project analyzed in ${data.meta.analysis_seconds}s`, "ok");
      renderReport(data);
    } catch (err) {
      setStatus("Network error: " + err.message, "err");
    }
  }

  // ---------- upload wiring ----------
  document.getElementById("zip-input").addEventListener("change", (e) => {
    if (!e.target.files.length) return;
    const fd = new FormData();
    fd.append("zipfile", e.target.files[0]);
    runAnalyze(fd);
  });

  document.getElementById("files-input").addEventListener("change", (e) => {
    if (!e.target.files.length) return;
    const fd = new FormData();
    [...e.target.files].forEach((f) => fd.append("files", f));
    runAnalyze(fd);
  });

  document.getElementById("run-sample").addEventListener("click", runSample);

  // convenience for local demos: /?autoload=sample runs the sample analysis on load
  if (new URLSearchParams(location.search).get("autoload") === "sample") {
    runSample();
  }

  const dropzone = document.getElementById("dropzone");
  ["dragenter", "dragover"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("drag-over");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("drag-over");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    const dropped = e.dataTransfer.files;
    if (!dropped.length) return;
    const fd = new FormData();
    if (dropped.length === 1 && dropped[0].name.endsWith(".zip")) {
      fd.append("zipfile", dropped[0]);
    } else {
      [...dropped].forEach((f) => fd.append("files", f));
    }
    runAnalyze(fd);
  });

  // ---------- rendering ----------
  function gateClassFor(value, goodMin, warnMin) {
    if (value >= goodMin) return "pass";
    if (value >= warnMin) return "warn";
    return "fail";
  }

  function renderReport(report) {
    lastReport = report;
    const s = report.summary;

    document.getElementById("project-title").textContent =
      report.meta.source === "bundled sample project"
        ? "Sample project: automated analysis"
        : "Uploaded project: automated analysis";
    document.getElementById("project-sub").textContent =
      `${report.meta.files_parsed} of ${report.meta.total_files_submitted} files parsed · ` +
      `${s.class_count} classes · ${s.total_logical_loc} logical LOC`;

    const gatePass = s.automated_quality_gate_pass_rate >= 70;
    const gateBadge = document.getElementById("gate-badge");
    gateBadge.className = "gate-badge " + (gatePass ? "gate-pass" : "gate-fail");
    document.getElementById("gate-badge-text").textContent =
      `${gatePass ? "Gate: healthy" : "Gate: attention needed"} — ${s.automated_quality_gate_pass_rate}% files passing`;

    renderTiles(s);
    renderCustomMetrics(s);
    renderFileTable(report.files);
    renderClassTable(report.classes);
    renderDuplicationTable(report.duplication.per_file);
    renderCharts(report.files);
  }

  function tile(label, value, sub, cls) {
    return `<div class="tile ${cls || ""}">
      <span class="tile-label">${label}</span>
      <span class="tile-value">${value}</span>
      <span class="tile-sub">${sub || ""}</span>
    </div>`;
  }

  function renderTiles(s) {
    const html = [
      tile("Logical LOC", s.total_logical_loc, `${s.total_physical_loc} physical lines`),
      tile("Avg. Complexity", s.avg_cyclomatic_complexity, "McCabe, per function",
        gateClassFor(10 - s.avg_cyclomatic_complexity, 5, 0)),
      tile("Maintainability", s.avg_maintainability_index, "Index, 0-100",
        gateClassFor(s.avg_maintainability_index, 65, 50)),
      tile("Duplication", s.project_duplication_pct + "%", "project-wide",
        gateClassFor(15 - s.project_duplication_pct, 10, 0)),
      tile("Avg. CBO", s.avg_cbo, `${s.class_count} classes`),
      tile("Avg. DIT", s.avg_dit, "inheritance depth"),
      tile("Avg. LCOM", s.avg_lcom, "lower is more cohesive"),
      tile("Metric Coverage", s.metric_coverage_ratio + "%", "files successfully scored",
        gateClassFor(s.metric_coverage_ratio, 95, 80)),
      tile("Gate Pass Rate", s.automated_quality_gate_pass_rate + "%", "automated verdicts",
        gateClassFor(s.automated_quality_gate_pass_rate, 70, 40)),
      tile("Classes analyzed", s.class_count, "OO design scope"),
    ];
    document.getElementById("tiles").innerHTML = html.join("");
  }

  function renderCustomMetrics(s) {
    document.getElementById("custom-grid").innerHTML = `
      <div class="custom-card">
        <div class="label">Metric Coverage Ratio (MCR)</div>
        <div class="value">${s.metric_coverage_ratio}%</div>
        <div class="desc">Share of submitted files the analyzer successfully parsed and scored across every configured metric. Files that fail to parse reduce this ratio and expose robustness gaps in the tool itself.</div>
      </div>
      <div class="custom-card">
        <div class="label">Automated Quality Gate Pass Rate (AQGPR)</div>
        <div class="value">${s.automated_quality_gate_pass_rate}%</div>
        <div class="desc">Share of analyzed files that automatically satisfy every configured quality threshold (complexity, maintainability, duplication). Validates that the rule engine produces trustworthy pass/fail verdicts.</div>
      </div>`;
  }

  function renderFileTable(files) {
    const tbody = document.querySelector("#file-table tbody");
    tbody.innerHTML = Object.entries(files).map(([name, d]) => `
      <tr>
        <td>${name}</td>
        <td>${d.loc.logical_loc}</td>
        <td>${d.complexity_avg}</td>
        <td>${d.complexity_max}</td>
        <td>${d.halstead.volume}</td>
        <td>${d.maintainability_index} (${d.maintainability_rating})</td>
        <td>${d.duplication_pct}%</td>
        <td><span class="badge ${d.quality_gate.passed ? "pass" : "fail"}">${d.quality_gate.passed ? "Pass" : "Fail"}</span></td>
      </tr>`).join("");
  }

  function renderClassTable(classes) {
    const tbody = document.querySelector("#class-table tbody");
    tbody.innerHTML = Object.entries(classes).map(([name, c]) => `
      <tr>
        <td>${name}</td>
        <td>${c.file}</td>
        <td>${c.method_count}</td>
        <td>${c.cbo}</td>
        <td>${c.dit}</td>
        <td>${c.lcom}</td>
      </tr>`).join("") || `<tr><td colspan="6" class="muted">No classes found in this project.</td></tr>`;
  }

  function renderDuplicationTable(perFile) {
    const tbody = document.querySelector("#dup-table tbody");
    tbody.innerHTML = Object.entries(perFile).map(([name, d]) => `
      <tr>
        <td>${name}</td>
        <td>${d.duplicated_lines}</td>
        <td>${d.countable_lines}</td>
        <td>${d.duplication_pct}%</td>
      </tr>`).join("");
  }

  function renderCharts(files) {
    if (typeof Chart === "undefined") return; // chart library failed to load - tiles/tables still work
    const labels = Object.keys(files);
    const complexityData = labels.map((f) => files[f].complexity_avg);
    const passCount = labels.filter((f) => files[f].quality_gate.passed).length;
    const failCount = labels.length - passCount;

    const ctx1 = document.getElementById("chart-complexity");
    if (complexityChart) complexityChart.destroy();
    complexityChart = new Chart(ctx1, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Avg. Cyclomatic Complexity",
          data: complexityData,
          backgroundColor: "#5B9BD9",
          borderRadius: 4,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#8A93A3", font: { size: 10 } }, grid: { color: "#1D2430" } },
          y: { ticks: { color: "#8A93A3" }, grid: { color: "#1D2430" }, beginAtZero: true },
        },
      },
    });

    const ctx2 = document.getElementById("chart-gate");
    if (gateChart) gateChart.destroy();
    gateChart = new Chart(ctx2, {
      type: "doughnut",
      data: {
        labels: ["Passing", "Failing"],
        datasets: [{ data: [passCount, failCount], backgroundColor: ["#3FBF8F", "#E2574C"], borderWidth: 0 }],
      },
      options: {
        plugins: { legend: { position: "bottom", labels: { color: "#E7EAEE", font: { size: 11 } } } },
      },
    });
  }

  // ---------- export ----------
  function download(filename, content, mime) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  document.getElementById("export-json").addEventListener("click", () => {
    if (!lastReport) return;
    download("asqma_report.json", JSON.stringify(lastReport, null, 2), "application/json");
  });

  document.getElementById("export-csv").addEventListener("click", () => {
    if (!lastReport) return;
    const rows = [["file", "logical_loc", "avg_complexity", "max_complexity", "halstead_volume", "maintainability_index", "duplication_pct", "gate_passed"]];
    Object.entries(lastReport.files).forEach(([name, d]) => {
      rows.push([name, d.loc.logical_loc, d.complexity_avg, d.complexity_max, d.halstead.volume, d.maintainability_index, d.duplication_pct, d.quality_gate.passed]);
    });
    const csv = rows.map((r) => r.join(",")).join("\n");
    download("asqma_report.csv", csv, "text/csv");
  });

  // ---------- sonarqube ----------
  function sonarConfig() {
    return {
      base_url: document.getElementById("sonar-url").value.trim(),
      token: document.getElementById("sonar-token").value.trim(),
      project_key: document.getElementById("sonar-project").value.trim(),
    };
  }

  function sonarStatus(msg, kind) {
    const el = document.getElementById("sonar-status");
    el.textContent = msg;
    el.className = "upload-status" + (kind ? " " + kind : "");
  }

  document.getElementById("sonar-test").addEventListener("click", async () => {
    sonarStatus("Testing connection...", "");
    try {
      const resp = await fetch("/api/sonarqube/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sonarConfig()),
      });
      const data = await resp.json();
      if (data.ok) sonarStatus("Connected to SonarQube server.", "ok");
      else sonarStatus("Connection failed: " + data.error, "err");
    } catch (err) {
      sonarStatus("Network error: " + err.message, "err");
    }
  });

  document.getElementById("sonar-fetch").addEventListener("click", async () => {
    sonarStatus("Fetching measures...", "");
    try {
      const resp = await fetch("/api/sonarqube/fetch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sonarConfig()),
      });
      const data = await resp.json();
      if (!data.ok) {
        sonarStatus("Fetch failed: " + data.error, "err");
        return;
      }
      sonarStatus("Measures retrieved and merged.", "ok");
      const tbody = document.querySelector("#sonar-table tbody");
      tbody.innerHTML = Object.entries(data.raw).map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join("");
    } catch (err) {
      sonarStatus("Network error: " + err.message, "err");
    }
  });
})();
