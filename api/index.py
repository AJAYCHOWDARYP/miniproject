import os
import sys
import traceback
from pathlib import Path

current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
backend_dir = root_dir / "backend"

paths_to_add = [
    str(root_dir),
    str(backend_dir),
    str(root_dir / "app"),
    str(backend_dir / "app"),
    str(current_dir)
]

for p in paths_to_add:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    try:
        from app.main import app
    except ImportError:
        from backend.app.main import app
    
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")

except Exception as err:
    err_details = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    
    app = FastAPI(title="Diagnostic Fallback")
    
    @app.get("/{path:path}")
    def error_page(path: str = ""):
        return HTMLResponse(
            content=f"""
            <div style="font-family: system-ui, sans-serif; padding: 2rem; max-width: 800px; margin: auto;">
                <h2 style="color: #e11d48;">Serverless Initialization Diagnostic</h2>
                <p>An error occurred while importing the application on Vercel:</p>
                <pre style="background: #f1f5f9; padding: 1rem; border-radius: 8px; overflow-x: auto; color: #0f172a;">{err_details}</pre>
                <p><strong>Python sys.path:</strong></p>
                <pre style="background: #f1f5f9; padding: 1rem; border-radius: 8px; overflow-x: auto;">{sys.path}</pre>
            </div>
            """,
            status_code=500
        )
    
    try:
        from mangum import Mangum
        handler = Mangum(app, lifespan="off")
    except Exception:
        handler = app
