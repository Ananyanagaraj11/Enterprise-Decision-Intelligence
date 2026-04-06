# CSV predictions & training check

## Why the dashboard might show only BENIGN

1. **No CSV analysis run yet**  
   The dashboard shows CSV results only after you run **CSV Analysis** (upload CSV → **Analyze File**). Until then, "Run Prediction" does a single live prediction (random features), which often returns BENIGN.

2. **Backend not running or not reachable**  
   The dashboard loads the last CSV result from `GET http://localhost:8000/api/last-analysis`. If the backend is not running or CORS blocks the request, no CSV data is loaded.

3. **Model has only one class or is not trained on attack types**  
   If `backend/artifacts` was never filled from training, or the model was trained on data that is mostly BENIGN, predictions will be mostly or only BENIGN. The dashboard only displays what the model returns.

## Flow that makes CSV predictions appear

1. **Start the backend**  
   From project root:  
   `python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000`  
   (or use `run_backend.bat`.)

2. **Run CSV Analysis**  
   - Open **CSV Analysis** (e.g. `http://localhost:9000/dashboard/analysis.html`).
   - Upload a CICIDS2017 CSV (with feature columns and optionally a `Label` column).
   - Click **Analyze File**.  
   The backend runs the model on the CSV, returns predictions (BENIGN, Bot, DDoS, PortScan, etc.), and **stores that result** for the dashboard.

3. **Open the Dashboard**  
   - Open **Dashboard** (e.g. `http://localhost:9000/dashboard/dashboard.html`).
   - On load, the dashboard calls **GET /api/last-analysis**. If you ran CSV Analysis in step 2, that returns the last result and the dashboard fills KPIs, charts, Recent Alerts, and the CSV table.
   - You can also click **Load CSV results** or **Run Prediction** to load the same stored result again.

So CSV predictions are produced by **/analyze/csv** and then served to the dashboard by **/api/last-analysis**. No training is required for this flow to work, but the **model** must already be trained and artifacts present (see below).

## Do you need to train?

**Train (and copy artifacts) if:**

- `backend/artifacts` is empty or missing `model.pt`, `scaler.joblib`, `classes.pt`, `feature_names.txt`.
- The backend was never set up with a trained model.
- You want the model to predict multiple attack types (e.g. Bot, DDoS, PortScan), but currently it only predicts BENIGN.

**Training steps (high level):**

1. Put CICIDS2017 (or UNSW-NB15) data in the expected folder (see `training/` and dataset loader).
2. Run training, e.g.:  
   `python training/train.py --data-dir <path> --use-cicids2017-dir --max-rows-total 50000`
3. Copy artifacts from `training/outputs/` to `backend/artifacts/`:  
   `copy_artifacts.bat` or manually copy `model.pt`, `scaler.joblib`, `classes.pt`, `feature_names.txt`.
4. Restart the backend.

After that, **Analyze File** on a CSV will use the new model and the dashboard will show the mix of classes (BENIGN + attacks) in charts and Recent Alerts.

## Quick checks

- **Backend has a model:**  
  Open `http://localhost:8000/health`. Response should include `"model_loaded": true` and `"classes": <number>`.

- **Backend has last CSV result:**  
  Open `http://localhost:8000/api/last-analysis`. If you ran CSV Analysis at least once, this returns JSON with `predictions` and `summary`. If it returns `null`, run CSV Analysis again, then reload the dashboard or click **Load CSV results**.

- **Model classes:**  
  Open `http://localhost:8000/config`. The `class_names` array should list all labels (e.g. BENIGN, Bot, DDoS, PortScan). If you only see one class, train with a dataset that includes multiple labels and copy artifacts again.
