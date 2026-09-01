import os
import sys
from pathlib import Path

# Set paths
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
backend_dir = root_dir / "backend"

for p in [str(root_dir), str(backend_dir), str(root_dir / "app"), str(backend_dir / "app"), str(current_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.main import app

# Top-level variables required by Vercel AST detector
handler = app
application = app
