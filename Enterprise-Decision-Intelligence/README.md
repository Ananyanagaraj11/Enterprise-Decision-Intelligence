# Enterprise Decision Intelligence (Agentic AI)

Course project for **CIS-600**: a **multi-stage analytics pipeline** on **daily e-commerce-style metrics**. It monitors KPIs, flags anomalies, attributes shifts to dimension splits (e.g. region / channel), ranks **predefined** corrective actions by utility, and renders explanations—implemented as a **central controller** plus **agents** with shared state (no LLM inventing the math).

## What it does

1. **Monitoring** — Rolling baseline and volatility on a chosen metric (e.g. revenue).
2. **Anomaly detection** — Deviation vs baseline with a confidence score.
3. **Root-cause style attribution** — Compares current vs baseline **per slice** when `rev_region_*` / `rev_channel_*` columns exist.
4. **Decision ranking** — Ranks entries from a fixed **playbook** (`enterprise_decision_intel/config.py`) using impact, risk, cost, and light context from the top attribution.
5. **Explanation** — Template text from structured outputs.

## Data

Public **BigQuery** datasets (no synthetic CSV committed here):

| Script | Output (default) |
|--------|------------------|
| `scripts/fetch_ga4_bigquery.py` | `data/ga4_public_daily.csv` — GA4 obfuscated sample |
| `scripts/fetch_thelook_bigquery.py` | `data/thelook_ecommerce_daily.csv` — The Look e-commerce (longer series, extra KPIs) |

After fetching, CSVs are **gitignored**; recreate them locally with the commands below.

## Setup

```bash
cd /path/to/Project

# Core pipeline
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional: BigQuery export
pip install -r requirements_fetch.txt
gcloud auth application-default login
# Set quota project if required:
# gcloud auth application-default set-quota-project YOUR_PROJECT_ID

python3 scripts/fetch_ga4_bigquery.py --out data/ga4_public_daily.csv
python3 scripts/fetch_thelook_bigquery.py --out data/thelook_ecommerce_daily.csv
```

### Run the pipeline (CLI)

```bash
python3 run.py --csv data/ga4_public_daily.csv
python3 run.py --csv data/thelook_ecommerce_daily.csv --metric revenue --json   # full JSONL
```

### Django dashboard

```bash
pip install -r requirements_django.txt
cd web_edi
python3 manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Choose dataset and metric in the UI (paths are relative to the **project root**).

### Evaluation

```bash
pip install -r requirements.txt
python3 scripts/evaluate.py --help
```

### Streamlit (optional)

```bash
pip install -r requirements_dashboard.txt
streamlit run dashboard/app.py
```

## Project layout

```
enterprise_decision_intel/   # Core package: config, pipeline, agents, evaluation
web_edi/                     # Django UI
scripts/                     # BigQuery fetch + evaluate
run.py                       # CLI runner
```

## Requirements

- Python **3.10+** recommended (3.9 may work with current pins).
- **Google Cloud** application-default credentials for BigQuery fetch scripts.

## License / course use

Academic / demonstration use for CIS-600. Tighten `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` before any public deployment.

Local proposal/interim PDFs are **not** tracked (see `.gitignore`); add them yourself if you need them in another fork.

## Publish to GitHub

This repo is ready to push (`main` branch, initial commit already created).

### Option A — GitHub CLI (recommended)

```bash
gh auth login
cd /path/to/Project
gh repo create enterprise-decision-intelligence --public --source=. --remote=origin --push
```

Use another repo name if you prefer. If the repo already exists on GitHub:

```bash
gh repo create YOUR_USERNAME/enterprise-decision-intelligence --public --source=. --remote=origin --push
```

### Option B — GitHub website

1. On GitHub: **New repository** → name it (e.g. `enterprise-decision-intelligence`) → **no** README / .gitignore (already in project) → Create.
2. Then:

```bash
cd /path/to/Project
git remote add origin https://github.com/YOUR_USERNAME/enterprise-decision-intelligence.git
git push -u origin main
```
