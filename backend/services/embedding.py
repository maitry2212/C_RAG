"""
Embedding service.
Logic from Notebook 3 — SentenceTransformer model.
"""

from sentence_transformers import SentenceTransformer

# Same model from Notebook 3 / 4
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Singleton model instance
_model = None


def get_embedding_model() -> SentenceTransformer:
    """Return the singleton embedding model."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def encode_documents(texts: list[str]) -> list:
    """Encode a list of text chunks into embeddings."""
    model = get_embedding_model()
    embeddings = model.encode(texts)
    return embeddings


def encode_query(query: str):
    """Encode a single query for retrieval."""
    model = get_embedding_model()
    return model.encode_query(query)
