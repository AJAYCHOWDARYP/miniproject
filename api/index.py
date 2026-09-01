import os
import sys
import traceback
from pathlib import Path

current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
backend_dir = root_dir / "backend"

for p in [str(root_dir), str(backend_dir), str(root_dir / "app"), str(backend_dir / "app"), str(current_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.main import app
    from mangum import Mangum
    mangum_handler = Mangum(app, lifespan="off")

    def handler(event, context):
        try:
            return mangum_handler(event, context)
        except Exception as e:
            tb = traceback.format_exc()
            return {
                "statusCode": 500,
                "headers": {"content-type": "text/html; charset=utf-8"},
                "body": f"<h2>Healthcare AI Assistant — Runtime Error:</h2><pre style='background:#f1f5f9;padding:15px;border-radius:8px;'>{tb}</pre>"
            }

except Exception as import_err:
    tb = traceback.format_exc()
    def handler(event, context):
        return {
            "statusCode": 500,
            "headers": {"content-type": "text/html; charset=utf-8"},
            "body": f"<h2>Healthcare AI Assistant — Startup Import Error:</h2><pre style='background:#f1f5f9;padding:15px;border-radius:8px;'>{tb}</pre><p>sys.path: {sys.path}</p>"
        }

application = handler
