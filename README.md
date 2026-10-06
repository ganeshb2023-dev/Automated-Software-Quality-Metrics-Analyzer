# Automated Software Quality Metrics Analyzer

A static-analysis web application that scores a Python codebase against
ten software metrics — eight industry-standard metrics and two metrics
designed specifically for this project — and renders the results on a
live dashboard. It can compute metrics locally (pure Python, no
external services required) and/or pull industry-benchmarked values
from a real SonarQube server.

This is the working implementation of the project described in
**Software Metrics Report 1**.

---

## 1. What's inside

```
asqma/
├── app.py                     Flask web application (routes / API)
├── analyzer/                  The metric computation engine
│   ├── loc.py                 Lines of Code
│   ├── complexity.py          Cyclomatic Complexity (McCabe)
│   ├── halstead.py            Halstead Complexity Measures
│   ├── oo_metrics.py          CBO, DIT, LCOM
│   ├── duplication.py         Code Duplication %
│   ├── maintainability.py     Maintainability Index
│   ├── custom_metrics.py      Metric Coverage Ratio + Automated Quality Gate Pass Rate
│   └── engine.py              Orchestrates all of the above into one report
├── sonarqube/
│   └── client.py              SonarQube Web API client (hybrid metric sourcing)
├── templates/index.html        Dashboard markup
├── static/css/style.css        Dashboard styling
├── static/js/dashboard.js      Dashboard behaviour (upload, charts, export)
├── sample_project/              3 demo Python files (clean / messy / OOP) to analyze instantly
├── tests/test_metrics.py       Unit + end-to-end tests for the engine
├── docker-compose.yml           Local SonarQube Community Edition + Postgres
├── sonar-project.properties     SonarScanner config for this repo
└── requirements.txt
```

## 2. How the 10 metrics map to the report

| # | Metric | Module | Category |
|---|---|---|---|
| 1 | Lines of Code (LOC) | `analyzer/loc.py` | Size |
| 2 | Cyclomatic Complexity | `analyzer/complexity.py` | Complexity |
| 3 | Halstead Complexity Measures | `analyzer/halstead.py` | Complexity / Volume |
| 4 | Coupling Between Objects (CBO) | `analyzer/oo_metrics.py` | OO Design |
| 5 | Depth of Inheritance Tree (DIT) | `analyzer/oo_metrics.py` | OO Design |
| 6 | Lack of Cohesion of Methods (LCOM) | `analyzer/oo_metrics.py` | OO Design |
| 7 | Code Duplication (%) | `analyzer/duplication.py` | Maintainability |
| 8 | Maintainability Index (MI) | `analyzer/maintainability.py` | Composite |
| 9 | **Metric Coverage Ratio (MCR)** — *own metric* | `analyzer/custom_metrics.py` | Project-specific |
| 10 | **Automated Quality Gate Pass Rate (AQGPR)** — *own metric* | `analyzer/custom_metrics.py` | Project-specific |

Every module's docstring explains the formula used and why. The two
custom metrics score the analyzer's **own** effectiveness — how
completely it processes a codebase (MCR) and how reliable its
automated pass/fail verdicts are (AQGPR) — which is what makes them
specific to an *"automated quality metrics analyzer"* rather than
generic code-quality indicators.

## 3. Quick start (local engine only, no SonarQube needed)

```bash
cd asqma
python3 -m venv .venv && source .venv/bin/activate     # optional but recommended
pip install -r requirements.txt
python3 app.py
```

Open **http://localhost:5000** and click **"Try sample project"** for
an instant demo, or drag-and-drop a `.zip` of any Python project (or
select individual `.py` files) onto the upload box.

Run the test suite at any time with:

```bash
python3 -m unittest discover -s tests -v
```

## 4. Adding real SonarQube into the loop

The dashboard's **SonarQube** tab lets you connect a running SonarQube
/ SonarCloud instance so the eight standard metrics can be
cross-checked against an industry-standard tool, exactly as described
in Report 1, Section 4.

**Option A — SonarCloud (fastest, no local install):**
1. Create a free account at sonarcloud.io and import this repository.
2. Generate a token under *My Account → Security*.
3. In the app's SonarQube tab, enter `https://sonarcloud.io`, your
   token, and the project key SonarCloud assigned.

**Option B — local SonarQube via Docker (fully offline demo):**
```bash
docker-compose up -d
# wait ~60s for SonarQube to finish starting, then open http://localhost:9000
# log in with admin / admin and set a new password
# My Account -> Security -> Generate Token
# Create a project with key "asqma-sample" (or edit sonar-project.properties)
```
Then run the scanner against this repo (requires the SonarScanner CLI;
see https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/):
```bash
sonar-scanner -Dsonar.host.url=http://localhost:9000 -Dsonar.token=<your token>
```
Once the scan finishes, paste `http://localhost:9000`, your token, and
`asqma-sample` into the app's SonarQube tab and click **"Fetch &
merge measures."**

> The local AST-based engine always computes **Metric Coverage Ratio**
> and **Automated Quality Gate Pass Rate** itself — SonarQube has no
> native equivalent for either, since both measure the analyzer's own
> behaviour rather than the analyzed code's.

## 5. API reference

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/` | Dashboard shell |
| `GET`  | `/api/sample` | Analyze the bundled `sample_project/` |
| `POST` | `/api/analyze` | Analyze an uploaded `.zip` (`zipfile` field) or `.py` files (`files` field) |
| `POST` | `/api/sonarqube/test` | `{base_url, token, project_key}` → connectivity check |
| `POST` | `/api/sonarqube/fetch` | `{base_url, token, project_key}` → fetch + map measures |

All analysis endpoints return the same report shape: `meta`, `summary`
(the 10 project-level metrics), `files` (per-file breakdown), `classes`
(per-class CBO/DIT/LCOM), and `duplication`.

## 6. Design notes & known limitations

- The engine analyzes **Python** source via the standard library's
  `ast` module — no third-party parser dependency, so it runs
  anywhere Python 3.9+ runs.
- Halstead, Cyclomatic Complexity, CBO, DIT and LCOM are implemented
  from their published formulas rather than wrapping an existing
  library, so the course project is demonstrably the student's own
  work; exact values may differ slightly from commercial tools using
  different token-classification rules — which is precisely why the
  SonarQube integration exists, to benchmark the local engine against
  an industry-standard implementation.
- `LCOM` uses the classic Chidamber & Kemerer LCOM1 definition, which
  includes constructors in the method set; a constructor that touches
  every field will raise a class's apparent cohesion, a well-documented
  property of LCOM1.
- Duplication detection uses a 4-line sliding-window hash; it catches
  copy-pasted blocks but not logic that is semantically similar yet
  textually different.
- The uploaded project is analyzed in a temporary directory that is
  deleted immediately after the report is generated — nothing is
  persisted server-side.

## 7. Suggested report-to-demo flow for submission

1. Run `python3 -m unittest discover -s tests -v` and screenshot the
   passing output as evidence the engine is correct.
2. Start the app, click **Try sample project**, and screenshot the
   Overview, File Metrics, OO Design and Duplication tabs.
3. Start SonarQube via `docker-compose up -d`, scan the repo, and
   screenshot the SonarQube tab after **Fetch & merge measures**.
4. Export the sample report as CSV/JSON (buttons on the File Metrics
   tab) and attach it as an appendix to Report 1.
