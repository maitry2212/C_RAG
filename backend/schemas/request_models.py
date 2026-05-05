"""
Request models for the API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""
    question: str = Field(..., description="The user's question")
    chat_id: int = Field(..., description="The context chat session id")


class URLIngestRequest(BaseModel):
    """Request body for URL-based ingestion."""
    url: str = Field(..., description="URL to scrape and ingest")
