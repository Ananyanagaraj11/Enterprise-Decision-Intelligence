# Full Prompts & Commands Reference

This file contains (1) the **original task prompts** used to build each component, and (2) **full runnable commands** for the project.

---

## Part 1: Original task prompts (specifications)

### Dataset loader

**Prompt:** You are a senior machine learning engineer.

Task: Write Python code to load a network intrusion detection dataset (UNSW-NB15 or CICIDS2017 CSV files), preprocess the data, and prepare it for deep learning training.

Requirements:
- Load CSV data using pandas
- Encode attack labels for multi-class classification
- Handle class imbalance
- Normalize numerical features using StandardScaler
- Remove non-informative identifiers
- Split data into train and validation sets (80/20)
- Return X_train, X_val, y_train, y_val
- Use clean, modular, production-ready code
- Use pandas, numpy, sklearn
- Output code only

---

### Training (PyTorch model)

**Prompt:** You are a machine learning engineer building a production-grade cyber attack detection model.

Task: Implement a deep learning model in PyTorch for multi-class intrusion detection.

Requirements:
- Input: preprocessed tabular network traffic features
- Model: Deep neural network (MLP or LSTM-ready structure)
- Loss: CrossEntropyLoss with class weights
- Optimizer: Adam
- Train for exactly 50 epochs
- Log training and validation loss per epoch
- Compute accuracy and macro F1-score per epoch
- Save trained model to disk
- Support GPU if available
- Clean and readable code
- Output code only

---

### Evaluation

**Prompt:** You are an applied machine learning engineer.

Task: Write Python code to evaluate a trained cyber attack detection model.

Requirements:
- Load saved PyTorch model
- Evaluate on validation data
- Compute accuracy, precision, recall, F1-score per class
- Generate and save confusion matrix
- Plot and save training curves
- Save evaluation metrics to a JSON file
- Use sklearn and matplotlib
- Output code only

---

### FastAPI backend

**Prompt:** You are a backend machine learning engineer.

Task: Build a FastAPI application to serve a trained cyber attack detection model.

Requirements:
- Load trained model and scaler at startup
- Accept network traffic feature input via POST /predict
- Return predicted attack class, confidence score, and threat severity
- Use Pydantic for request validation
- Enable CORS support
- Structure code for production readiness
- Output code only

---

### Explainability (SHAP)

**Prompt:** You are a machine learning engineer specializing in explainable AI.

Task: Implement SHAP-based feature importance for cyber attack predictions.

Requirements:
- Use SHAP for tabular deep learning models
- Compute feature contributions for a single prediction
- Return top contributing features with importance scores
- Integrate with the FastAPI backend
- Optimize for inference speed
- Output code only

---

### Streamlit dashboard

**Prompt:** You are a data scientist building a security operations center (SOC) dashboard.

Task: Create an interactive Streamlit dashboard for cyber attack detection.

Requirements:
- Input controls for simulated network traffic features
- Call FastAPI backend for predictions
- Display predicted attack type and threat severity
- Visualize attack trends over time
- Show SHAP feature importance plots
- Include dataset statistics and model performance metrics
- Clean, professional SOC-style layout
- Output code only

---

### README

**Prompt:** You are a senior machine learning engineer.

Task: Write a professional GitHub README for an AI-powered cyber threat intelligence dashboard.

Requirements:
- Clear problem statement
- Dataset description
- Machine learning approach
- System architecture
- Technology stack
- Instructions to run locally
- Future improvements
- Use clean and structured markdown

---

## Part 2: Full runnable commands

### One-time setup (Windows)

```cmd
cd "C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
scripts\setup_windows.bat
```

(Install Python from https://www.python.org/downloads/ with “Add python.exe to PATH” first if needed; see INSTALL_PYTHON.md.)

---

### Train (replace with your CSV path)

```cmd
cd "C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
venv\Scripts\activate
python training/train.py --data data/UNSW_NB15_traintest.csv --out-dir training/outputs --epochs 50
```

Quick test (fewer rows, fewer epochs):

```cmd
python training/train.py --data data/your_file.csv --out-dir training/outputs --max-rows 50000 --epochs 10
```

---

### Copy artifacts to backend

```cmd
cd "C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
scripts\copy_artifacts.bat
```

Or manually:

```cmd
mkdir backend\artifacts 2>nul
copy training\outputs\model.pt backend\artifacts\
copy training\outputs\scaler.joblib backend\artifacts\
copy training\outputs\classes.pt backend\artifacts\
copy training\outputs\feature_names.txt backend\artifacts\
```

---

### Evaluate

```cmd
cd "C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
venv\Scripts\activate
python training/evaluate.py --model-dir training/outputs --data data/UNSW_NB15_traintest.csv --out-dir training/outputs
```

---

### Start backend (Terminal 1)

```cmd
cd "C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
scripts\run_backend.bat
```

Or:

```cmd
venv\Scripts\activate
python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

---

### Start dashboard (Terminal 2)

```cmd
cd "C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
scripts\run_dashboard.bat
```

Or:

```cmd
venv\Scripts\activate
python -m streamlit run dashboard/streamlit_app.py
```

---

### Full pipeline (copy-paste sequence)

```cmd
cd "C:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
scripts\setup_windows.bat
venv\Scripts\activate
python training/train.py --data data/UNSW_NB15_traintest.csv --out-dir training/outputs --epochs 50
scripts\copy_artifacts.bat
python training/evaluate.py --model-dir training/outputs --data data/UNSW_NB15_traintest.csv --out-dir training/outputs
```

Then in one terminal: `scripts\run_backend.bat`  
In another: `scripts\run_dashboard.bat`

---

## Project overview prompt (for context)

**High-level prompt:** AI-Powered Cyber Attack Detection & Threat Intelligence Dashboard

This project is an end-to-end machine learning system for detecting and classifying cyber attacks using real-world network traffic data. The system trains deep learning models on network intrusion datasets to identify malicious activity, assigns threat severity scores, and explains model decisions using explainable AI techniques.

The trained models are deployed via a FastAPI backend for real-time inference, and an interactive SOC-style dashboard visualizes live predictions, attack trends, traffic patterns, and feature importance. The goal is to simulate a production-grade cyber threat intelligence platform used in real-world security operations centers (SOC).

Key objectives:
- Train deep learning models for multi-class cyber attack detection
- Handle class imbalance and temporal network behavior
- Serve ML predictions through a scalable backend API
- Visualize attack patterns, alerts, and explanations in an interactive dashboard
- Build a system that mirrors real-world cybersecurity analytics pipelines
