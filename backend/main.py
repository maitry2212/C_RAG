"""
CRAG Pipeline FastAPI Backend
Main entry point — run with: uvicorn main:app --reload
"""

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.ingest import router as ingest_router
from api.query import router as query_router
from api.graph import router as graph_router

app = FastAPI(
    title="CRAG Pipeline API",
    description="Corrective RAG pipeline backend for document Q&A",
    version="1.0.0",
)

# CORS — allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(ingest_router, tags=["Ingest"])
app.include_router(query_router, tags=["Query"])
app.include_router(graph_router, tags=["Graph"])


@app.get("/health")
def health():
    """Returns server status."""
    return {"status": "ok"}
