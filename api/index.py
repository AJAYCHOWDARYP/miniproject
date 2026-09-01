import os
import sys
from pathlib import Path

# Add backend and root paths so modules import cleanly in Vercel Serverless
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
backend_dir = root_dir / "backend"

for p in [str(backend_dir), str(root_dir), str(backend_dir / "app")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.main import app

try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except Exception:
    handler = app
