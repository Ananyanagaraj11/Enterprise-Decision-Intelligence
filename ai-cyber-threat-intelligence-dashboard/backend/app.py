from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import torch
from torch import nn
import torch.serialization
import numpy
import joblib
import numpy as np
from pathlib import Path
import pandas as pd
from io import StringIO
from typing import List

app = FastAPI()

# ========================= CORS =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================= MODEL =========================
class CyberThreatModel(nn.Module):
    def __init__(self, input_dim, num_classes, hidden_dims=[128, 64], dropout=0.3):
        super().__init__()
        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim

        self.backbone = nn.Sequential(*layers)
        self.head = nn.Linear(prev_dim, num_classes)

    def forward(self, x):
        x = self.backbone(x)
        return self.head(x)

# ========================= LOAD MODEL =========================
artifacts_dir = Path("backend/artifacts")
device = torch.device("cpu")

model = None
scaler = None
classes = []
feature_names = []

try:
    # 🔐 Fix for PyTorch 2.6+
    torch.serialization.add_safe_globals(
        [numpy._core.multiarray._reconstruct]
    )

    classes = torch.load(
        artifacts_dir / "classes.pt",
        map_location=device,
        weights_only=False
    )

    scaler = joblib.load(artifacts_dir / "scaler.joblib")

    with open(artifacts_dir / "feature_names.txt", "r") as f:
        feature_names = [line.strip() for line in f]

    checkpoint = torch.load(
        artifacts_dir / "model.pt",
        map_location=device,
        weights_only=False
    )

    input_dim = checkpoint.get("input_dim", len(feature_names))
    num_classes = checkpoint.get("num_classes", len(classes))
    hidden_dims = checkpoint.get("hidden_dims", [128, 64])
    dropout = checkpoint.get("dropout", 0.3)

    model = CyberThreatModel(input_dim, num_classes, hidden_dims, dropout)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    print("[OK] Model loaded successfully")

except Exception as e:
    print("[ERROR] Model load error:", e)

# ========================= MEMORY STORE =========================
last_analysis_store = {}

# ========================= REQUEST MODELS =========================
class PredictionRequest(BaseModel):
    features: List[float]

# ========================= STATIC DASHBOARD =========================
_dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"
if _dashboard_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(_dashboard_dir), html=True), name="dashboard")

@app.get("/")
def root():
    return RedirectResponse(url="/dashboard/index.html", status_code=302)

# ========================= HEALTH =========================
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None
    }

# ========================= LOAD LAST ANALYSIS =========================
@app.get("/api/last-analysis")
def get_last_analysis():
    return last_analysis_store.get("data")

# ========================= SINGLE PREDICTION =========================
@app.post("/predict")
def predict(request: PredictionRequest):

    if model is None:
        return {"error": "Model not loaded"}

    features = np.array(request.features).reshape(1, -1)
    features = np.nan_to_num(features)

    features_scaled = scaler.transform(features)

    with torch.no_grad():
        outputs = model(torch.FloatTensor(features_scaled))
        probs = torch.softmax(outputs, dim=1)
        idx = torch.argmax(probs, dim=1).item()
        confidence = probs[0][idx].item()

    return {
        "predicted_class": classes[idx],
        "confidence": confidence
    }

# ========================= CSV ANALYSIS =========================
@app.post("/analyze/csv")
async def analyze_csv(file: UploadFile = File(...)):
    if model is None:
        return {"success": False, "error": "Model not loaded"}
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))

        original_row_count = len(df)

        # Detect label column
        label_col = None
        if "Label" in df.columns:
            label_col = "Label"
        elif " Label" in df.columns:
            label_col = " Label"

        actual_labels = None
        if label_col:
            actual_labels = df[label_col].values
            df = df.drop(columns=[label_col])

        numeric_df = df.select_dtypes(include=[np.number])
        numeric_df = numeric_df.replace([np.inf, -np.inf], np.nan).fillna(0)

        original_row_count = len(numeric_df)

        features = numeric_df.values
        features_scaled = scaler.transform(features)

        with torch.no_grad():
            outputs = model(torch.FloatTensor(features_scaled))
            probabilities = torch.softmax(outputs, dim=1)
            predicted_indices = torch.argmax(probabilities, dim=1)

        predicted_indices = predicted_indices.numpy()
        probabilities = probabilities.numpy()

        predictions = []
        class_counts = {}

        for i in range(len(features)):
            predicted_class = classes[predicted_indices[i]]
            confidence = float(probabilities[i][predicted_indices[i]])

            class_counts[predicted_class] = class_counts.get(predicted_class, 0) + 1

            pred_obj = {
                "index": i,
                "predicted_class": predicted_class,
                "confidence": confidence
            }

            if actual_labels is not None:
                pred_obj["actual_label"] = str(actual_labels[i])

            predictions.append(pred_obj)

        attack_count = sum(
            count for cls, count in class_counts.items() if cls != "BENIGN"
        )

        # Confidence buckets: 0-20%, 20-40%, 40-60%, 60-80%, 80-100% (inclusive boundaries)
        confidence_buckets = [0, 0, 0, 0, 0]
        for i in range(len(probabilities)):
            pct = round(float(probabilities[i][predicted_indices[i]]) * 100)
            pct = max(0, min(100, pct))
            if pct <= 20:
                idx = 0
            elif pct <= 40:
                idx = 1
            elif pct <= 60:
                idx = 2
            elif pct <= 80:
                idx = 3
            else:
                idx = 4
            confidence_buckets[idx] += 1

        result = {
            "success": True,
            "total_rows": original_row_count,
            "predictions": predictions[:1000],  # send up to 1000 for dashboard table; summary is from full analysis
            "summary": {
                "class_distribution": class_counts,
                "total_attacks": attack_count,
                "total_benign": class_counts.get("BENIGN", 0),
                "attack_percentage": (attack_count / original_row_count * 100),
                "confidence_buckets": confidence_buckets,
            }
        }

        last_analysis_store["data"] = result

        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# ========================= START SERVER =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)