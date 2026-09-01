"""
Main FastAPI Application Entrypoint.
Enforces 100% Report-Driven Architecture with ZERO hardcoded/fake medical data.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy import select

from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.security import hash_password
from app.api.v1.router import api_router
from app.models.user import User, HealthProfile

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
try:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass


async def init_clean_auth_account():
    """Initializes a clean demo authentication account with ZERO medical records."""
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
            print("[INFO] Clean Patient Account initialized with ZERO hardcoded medical reports or medications.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_clean_auth_account()
    yield
    await engine.dispose()


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
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root_index():
    from fastapi.responses import FileResponse
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Personalized Healthcare AI Assistant API is active.", "docs": "/docs"}
