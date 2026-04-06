# Demo URL – One link for the app

The backend now serves the dashboard. You only need **one server** and **one URL**.

## Run the app (local)

1. Start the backend (from project root):
   ```bash
   python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
   ```
   Or double‑click `scripts\run_backend.bat`.

2. Open in browser:
   - **http://localhost:8000** → redirects to the dashboard
   - Or **http://localhost:8000/dashboard/index.html**

No need to run a separate frontend server on port 9000 for the demo.

---

## Shareable demo URL (e.g. for LinkedIn)

To get a **public link** others can open:

1. Install **ngrok**: https://ngrok.com/download (or `choco install ngrok`).

2. Start the backend (step 1 above). Keep it running.

3. In a new terminal run:
   ```bash
   ngrok http 8000
   ```

4. Copy the **HTTPS** URL ngrok shows (e.g. `https://abc123.ngrok-free.app`).

5. Share that URL. Anyone opening it will see:
   - **https://your-id.ngrok-free.app** → dashboard (Index → CSV Analysis → Dashboard).

Use this link in your LinkedIn post or video description.

---

## Optional: local frontend on port 9000

If you still run `python -m http.server 9000` and open **http://localhost:9000/dashboard/index.html**, the app will use the backend at **http://localhost:8000** as before.
