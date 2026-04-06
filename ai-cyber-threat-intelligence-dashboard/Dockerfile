# Live demo / production image: API + dashboard on one server
# Uses requirements-render.txt (slim + CPU-only PyTorch) for faster builds
FROM python:3.11-slim

WORKDIR /app

# Install deps (slim list + CPU-only torch = much faster than full requirements.txt)
COPY requirements-render.txt .
RUN pip install --no-cache-dir -r requirements-render.txt

# App code + artifacts (must have backend/artifacts with model)
COPY backend ./backend
COPY dashboard ./dashboard

# Ensure artifacts exist (build will fail if not)
RUN test -f backend/artifacts/model.pt || (echo "Missing backend/artifacts - run copy_artifacts first" && exit 1)

EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
