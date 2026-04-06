# Portfolio & GitHub Update Guide

Use the text below to update your portfolio (LinkedIn, personal site, resume) and GitHub.

---

## 1. GitHub repo (soc-lite-ai-ids)

### Repo description (short)
Paste in **GitHub → repo → About → Description**:

```
SOC-style AI dashboard for network intrusion detection. PyTorch MLP + FastAPI + Plotly. CICIDS2017, CSV analysis, live demo on GitHub Pages + Render.
```

### Topics (GitHub → About → Topics)
Add or keep:
```
cybersecurity  machine-learning  pytorch  fastapi  intrusion-detection  threat-detection  dashboard  ids  cicids2017
```

### Repo URL (after you renamed)
```
https://github.com/Ananyanagaraj11/soc-lite-ai-ids
```

### Live demo URL (if you use GitHub Pages)
```
https://ananyanagaraj11.github.io/ai-cyber-threat-dashboard/
```
*(If you rename the repo, GitHub Pages URL may change to `.../soc-lite-ai-ids/` if you use that repo for Pages.)*

---

## 2. Portfolio / LinkedIn project entry

**Project name:** SOC Lite – AI-Powered Intrusion Detection System

**One-liner:**
Real-time network intrusion detection dashboard with ML-based attack classification and a SOC-style UI.

**Description (short):**
- Built an end-to-end ML pipeline for detecting and classifying cyber attacks from network traffic (CICIDS2017).
- Backend: FastAPI + PyTorch MLP; frontend: HTML/CSS/JS + Plotly for KPIs, attack distribution, and CSV batch analysis.
- Deployed frontend on GitHub Pages and backend on Render; configurable for local run (localhost:8000 + 9001).

**Tech stack:** Python, PyTorch, FastAPI, pandas, scikit-learn, Plotly.js, HTML/CSS/JavaScript

**Links:**
- Repo: https://github.com/Ananyanagaraj11/soc-lite-ai-ids
- Live demo: https://ananyanagaraj11.github.io/ai-cyber-threat-dashboard/ (or your Vercel/Render URL)

---

## 3. GitHub profile README (if you use one)

Add a project card or line:

```markdown
### SOC Lite – AI IDS Dashboard
🛡️ Network intrusion detection with PyTorch + FastAPI. [Repo](https://github.com/Ananyanagaraj11/soc-lite-ai-ids) · [Live demo](https://ananyanagaraj11.github.io/ai-cyber-threat-dashboard/)
```

---

## 4. Resume / CV bullet (example)

- **SOC Lite AI IDS:** Developed an ML-powered intrusion detection dashboard (PyTorch, FastAPI, Plotly); supports CSV batch analysis and real-time KPIs; deployed on GitHub Pages and Render.

---

After updating, push the README changes:

```bash
cd "c:\Users\anany\Downloads\New folder (2)\ai-cyber-threat-intelligence-dashboard"
git add README.md PORTFOLIO_AND_GITHUB.md
git commit -m "README: repo name soc-lite-ai-ids, add portfolio/GitHub guide"
git push origin main
```

*(Use `python_portable\python.exe` or your Git path if needed.)*
