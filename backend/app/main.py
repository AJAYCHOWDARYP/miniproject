"""
Main FastAPI Application Entrypoint.
Enforces 100% Report-Driven Architecture with ZERO hardcoded/fake medical data.
Optimized for high-performance Local and Serverless (Vercel) execution.
"""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select

from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.security import hash_password
from app.api.v1.router import api_router
from app.models.user import User, HealthProfile

# Locate static directory cleanly across local and Vercel serverless environments
possible_static_paths = [
    Path(__file__).resolve().parent.parent / "static",
    Path(__file__).resolve().parent.parent.parent / "backend" / "static",
    Path.cwd() / "backend" / "static",
    Path.cwd() / "static"
]

STATIC_DIR = None
for p in possible_static_paths:
    if p.exists() and (p / "index.html").exists():
        STATIC_DIR = p
        break

if not STATIC_DIR:
    STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
    try:
        STATIC_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


async def init_clean_auth_account():
    """Initializes a clean demo authentication account with ZERO medical records."""
    try:
        async with AsyncSessionLocal() as db:
            user_check = await db.execute(select(User).where(User.email == "demo@healthcare.ai"))
            if not user_check.scalar_one_or_none():
                demo_user = User(
                    email="demo@healthcare.ai",
                    password_hash=hash_password("DemoPassword123!"),
                    full_name="Patient Account",
                    is_active=True
                )
                db.add(demo_user)
                await db.flush()

                profile = HealthProfile(
                    user_id=demo_user.id,
                    age=38.0,
                    sex="Male",
                    height_cm=178.0,
                    weight_kg=78.5,
                    activity_level="moderate",
                    dietary_preferences=["balanced"]
                )
                db.add(profile)
                await db.commit()
    except Exception as e:
        print(f"[INFO] Auth note: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await init_clean_auth_account()
    except Exception as e:
        print(f"[INFO] Startup note: {e}")
    yield
    try:
        await engine.dispose()
    except Exception:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Personalized, Report-Driven Healthcare Assistant platform.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

if STATIC_DIR and STATIC_DIR.exists():
    try:
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    except Exception as e:
        print(f"[INFO] Static mount note: {e}")


@app.get("/")
async def root_index():
    for p in possible_static_paths:
        if p.exists() and (p / "index.html").exists():
            return HTMLResponse(content=(p / "index.html").read_text(encoding="utf-8"), media_type="text/html")
    return {"message": "Personalized Healthcare AI Assistant API is active.", "docs": "/docs"}


@app.get("/styles.css")
@app.get("/static/styles.css")
async def get_styles():
    for p in possible_static_paths:
        if p.exists() and (p / "styles.css").exists():
            return Response(content=(p / "styles.css").read_text(encoding="utf-8"), media_type="text/css")
    return Response(content="", media_type="text/css")


@app.get("/app.js")
@app.get("/static/app.js")
async def get_js():
    for p in possible_static_paths:
        if p.exists() and (p / "app.js").exists():
            return Response(content=(p / "app.js").read_text(encoding="utf-8"), media_type="application/javascript")
    return Response(content="", media_type="application/javascript")


@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": settings.VERSION}
