import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from openenv.core.env_server import create_fastapi_app

# --- FIXED IMPORTS ---
from ticket_triage.server.environment import TicketTriageEnvironment
from ticket_triage.models import TriageAction, TriageObservation
# ---------------------

# 1. Initialize the OpenEnv FastAPI application
app = create_fastapi_app(TicketTriageEnvironment, TriageAction, TriageObservation)

# 2. Add the UI Route (Defining it as a function first is safer for some frameworks)
async def get_ui_content():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Enterprise Incident Commander</title>
            <style>
                body { font-family: system-ui, -apple-system, sans-serif; background-color: #0f172a; color: #e2e8f0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .card { background-color: #1e293b; padding: 3rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); text-align: center; border: 1px solid #334155; }
                h1 { color: #f8fafc; margin-bottom: 0.5rem; letter-spacing: -0.025em; }
                .status { display: inline-flex; align-items: center; gap: 0.5rem; background-color: #064e3b; color: #34d399; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 600; margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 0.05em; }
                .dot { width: 8px; height: 8px; background-color: #34d399; border-radius: 50%; box-shadow: 0 0 8px #34d399; animation: pulse 2s infinite; }
                code { background-color: #020617; padding: 0.75rem 1rem; border-radius: 6px; color: #38bdf8; font-family: monospace; font-size: 1rem; border: 1px solid #1e293b; }
                p { margin-bottom: 1.5rem; color: #94a3b8; }
                @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🚨 Incident Commander</h1>
                <div class="status"><div class="dot"></div> Server Online</div>
                <p>The OpenEnv RL Environment is actively listening for AI agents.</p>
                <code>WebSocket Endpoint Ready</code>
                <p>The OpenEnv RL Environment is actively listening for AI agents.</p>
                <a href="/docs" target="_blank" style="color: #38bdf8; text-decoration: none; border: 1px solid #38bdf8; padding: 5px 10px; border-radius: 4px;">Open API Docs</a>
            </div>
        </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
@app.get("/web", response_class=HTMLResponse)
async def root_ui():
    return await get_ui_content()

# Required by the OpenEnv multi-mode deployment validator
def main():
    uvicorn.run("ticket_triage.server.app:app", host="0.0.0.0", port=7860, reload=False)

if __name__ == "__main__":
    main()