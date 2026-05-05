"""
CRAG Pipeline FastAPI Backend
Main entry point — run with: uvicorn main:app --reload
"""

import os
import sys
import asyncio
import logging
from contextlib import asynccontextmanager

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.ingest import router as ingest_router
from api.query import router as query_router
from api.graph import router as graph_router
from api.auth import router as auth_router
from api.chats import router as chats_router
from core.database import init_db

# ── Logging ──────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("crag")

# ── CORS origins from env ────────────────────────
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create NeonDB tables on application startup."""
    init_db()
    logger.info("Database tables verified / created.")
    yield

app = FastAPI(
    title="CRAG Pipeline API",
    description="Corrective RAG pipeline backend for document Q&A",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(chats_router, prefix="/chats", tags=["Chats"])
app.include_router(ingest_router, tags=["Ingest"])
app.include_router(query_router, tags=["Query"])
app.include_router(graph_router, tags=["Graph"])


@app.get("/health")
def health():
    """Returns server status."""
    return {"status": "ok"}
