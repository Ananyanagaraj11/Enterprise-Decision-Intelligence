# Autonomous Enterprise Decision Intelligence (Agentic AI)

**CIS 600 — Syracuse University**

This package is part of the [Enterprise-Decision-Intelligence](https://github.com/Ananyanagaraj11/Enterprise-Decision-Intelligence) monorepo. It contains the course project notebook, sample data, written report, slides, and a reference code archive.

## Authors

- **Ananya Naga Raj** (SUID 214585923)
- **Abhijnya Konanduru Gurumurthy** (SUID 231885826)
- **Amulya Naga Raj** (SUID 286373513)
- **Sunil Hanumanthegowda Kote** (SUID 324362001)

## What this is

An **autonomous enterprise decision intelligence** prototype that watches daily business metrics, flags anomalies, attributes impact across dimensions, ranks corrective actions with a utility model, and emits structured explanations. Agents follow a **perception → reasoning → action → feedback** loop coordinated by a **rule-based Central Controller** and **Shared Memory**.

### Pipeline (execution order)

| Stage | Role |
|--------|------|
| **Monitoring Agent** | Ingests daily series; rolling mean / std and EWMA baselines |
| **Anomaly Detection Agent** | Blended z-score from rolling and EWMA deviation; confidence and flags |
| **Root Cause Agent** | Contribution-based attribution across business dimensions |
| **Decision Agent** | Ranks a fixed playbook of interventions (impact, risk, cost) with context boosts |
| **Explanation Agent** | Template narrative from computed stats; optional LLM if configured |
| **Central Controller** | Orchestrates stages, thresholds, validation, and re-evaluation on conflict |

### Evaluation

The notebook compares the full agentic stack to **three non-agentic baselines** using precision, recall, F1, detection latency, root-cause accuracy (top-1 / top-3), utility gain, Kendall τ consistency, paired tests across seeds, and confidence calibration.

## Contents

| File | Description |
|------|-------------|
| `Autonomous Enterprise Decision Intelligence.ipynb` | Full implementation, experiments, and figures |
| `ga4_public_daily.csv` | Daily extract aligned with the GA4 public e-commerce style schema used in the notebook |
| `Autonomous Enterprise Decision Intelligence Using Agentic AI Final Report.pdf` | Project report |
| `CIS 600-Agentic AI-AUTONOMOUS ENTERPRISE DECISION INTELLIGENCE-Project Presentation.pptx` | Presentation |
| `Enterprise-Decision-Intelligence-main (1).zip` | Reference snapshot of related application code (optional) |

## Requirements

- **Python** 3.10+ (notebook metadata targets 3.10)
- **Packages:** `numpy`, `pandas`, `scipy`, `matplotlib`

Install:

```bash
pip install numpy pandas scipy matplotlib
```

Use **Jupyter Lab**, **VS Code**, or **Google Colab**.

## Data

`ga4_public_daily.csv` is built from the **[Google Analytics 4 BigQuery public e-commerce sample](https://support.google.com/analytics/answer/9358801)** (obfuscated), aggregated to **daily** granularity for this project. The notebook’s `load_ga4_style_csv` expects a CSV with a `date` column plus revenue, KPIs, and optional `rev_region_*` / `rev_channel_*` style dimension columns.

## Running the notebook

1. Open `Autonomous Enterprise Decision Intelligence.ipynb`.
2. Run the **Imports and Setup** cell (`pip install` is included for Colab).
3. **Dataset cell**
   - **Google Colab:** use the provided `files.upload()` cell and upload `ga4_public_daily.csv`.
   - **Local Jupyter:** skip Colab-only imports and set the path explicitly, for example:

     ```python
     from pathlib import Path
     CSV_PATH = Path("ga4_public_daily.csv").resolve()
     df = load_ga4_style_csv(CSV_PATH)
     ```

     Keep the CSV in **this same folder** as the notebook (or pass any absolute path).

4. Run the remaining cells in order for the full pipeline and evaluation sections.

## Optional LLM explanations

The **Explanation Agent** uses a deterministic template by default. To call an external LLM for wording only (inputs are precomputed metrics), set:

| Variable | Purpose |
|----------|---------|
| `LLM_API_ENDPOINT` | HTTP API base URL |
| `LLM_API_KEY` | API key |
| `LLM_MODEL` | Model name (default in code: `gpt-4o-mini`) |

If the call fails or variables are unset, the notebook falls back to the template.

## Citation / course context

Course deliverable for **CIS 600 (Agentic AI)** — autonomous monitoring, attribution, and decision support over operational analytics, with explicit evaluation against simpler baselines.
