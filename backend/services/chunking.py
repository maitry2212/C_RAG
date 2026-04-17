"""
Chunking service.
Logic from Notebook 3 — RecursiveCharacterTextSplitter.
"""

from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Default config from Notebook 3 / 4
CHUNK_SIZE = 500
CHUNK_OVERLAP = 75


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into chunks using RecursiveCharacterTextSplitter.
    Exact logic from Notebook 3.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(text)
    return chunks
