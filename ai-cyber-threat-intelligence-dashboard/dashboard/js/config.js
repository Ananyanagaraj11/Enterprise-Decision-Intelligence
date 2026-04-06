// Backend API URL. Local: use 127.0.0.1:8000 when frontend is on localhost (e.g. port 9001). Else: Render for deploy.
if (typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")) {
  window.ENV_API_BASE = "http://localhost:8000";
} else {
  window.ENV_API_BASE = window.ENV_API_BASE || "https://ai-cyber-threat-dashboard-1.onrender.com";
}
