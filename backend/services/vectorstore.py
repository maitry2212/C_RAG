"""
Vector store service.
Logic from Notebook 3 — Qdrant in-memory client.
"""

import os
import uuid
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from services.embedding import encode_documents, encode_query

# Qdrant client
COLLECTION_NAME = "documents"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output dim

# Persistent local path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", ".qdrant_data")

# Singleton client
_client = None


def get_client() -> QdrantClient:
    """Return the singleton Qdrant persistent client."""
    global _client
    if _client is None:
        _client = QdrantClient(path=DB_PATH)
    return _client


def _ensure_collection():
    """Create the collection if it doesn't exist."""
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )


def reset_collection():
    """Delete and recreate the collection (for fresh ingest)."""
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in collections:
        client.delete_collection(collection_name=COLLECTION_NAME)
    _ensure_collection()


def store_chunks(chunks: List[str]):
    """
    Encode chunks and store them in Qdrant.
    """
    _ensure_collection()
    client = get_client()

    emd_docs = encode_documents(chunks)

    points = [
        PointStruct(
            id=uuid.uuid4().hex,
            vector=emd_docs[i],
            payload={"text": chunks[i]}
        )
        for i in range(len(chunks))
    ]

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    return len(points)


def query_vectors(query: str, limit: int = 3):
    """
    Query the vector store.
    Exact logic from Notebook 3.
    """
    _ensure_collection()
    client = get_client()

    query_vector = encode_query(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit
    )

    return results
