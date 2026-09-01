import os
import sys
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

from app.main import app
from mangum import Mangum

# Wrap FastAPI ASGI app into standard AWS Lambda / Vercel Serverless handler
handler = Mangum(app, lifespan="off")
application = handler
