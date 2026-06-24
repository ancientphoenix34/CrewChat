from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.auth.router import router as auth_router
from src.channels.router import router as channels_router
from src.dms.router import router as dms_router
from src.core.config import settings
from src.core.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
     await init_db()
     yield

app = FastAPI(
    title="Crewchat API",
    version="0.1.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    lifespan=lifespan,
)

#.add_middleware() is just a FastAPI/Starlette method
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(channels_router) 
app.include_router(dms_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

