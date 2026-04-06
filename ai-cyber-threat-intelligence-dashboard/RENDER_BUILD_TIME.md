# Faster Render builds

Render was taking ~25 minutes because of:
- **PyTorch** (large download, especially with default CUDA)
- **Extra packages** (jupyter, streamlit, matplotlib, shap) not needed at runtime

## What we did

- **`requirements-render.txt`** – Slim list for deploy only: torch (CPU), pandas, sklearn, FastAPI, uvicorn, etc. No jupyter/streamlit/matplotlib/shap.
- **CPU-only PyTorch** – In that file we use `--extra-index-url https://download.pytorch.org/whl/cpu` so Pip installs the smaller CPU build.
- **Dockerfile** and **render.yaml** now use `requirements-render.txt` for the build.

## What to expect

- **First deploy** after this change may still take ~10–15 min (PyTorch CPU is still big).
- **Later deploys** should be faster when Render reuses cached layers (often 3–8 min when only your code changes).

## If Render is still using Docker

If your service was created with **Docker**, it will use the Dockerfile (already updated). If it was created with **Python**, it will use `render.yaml` and the new build command. Both paths now use the slim requirements.

## Full stack (local/dev)

For local work with training, Jupyter, Streamlit, etc., keep using:

```bash
pip install -r requirements.txt
```
