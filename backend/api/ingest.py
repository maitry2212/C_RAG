"""
Ingest API route.
POST /ingest — accepts file upload or URL.
"""

import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from api.auth import get_current_user
import sys
import asyncio

from services.preprocessing import process_text_to_markdown
from services.chunking import chunk_text
from services.vectorstore import store_chunks, reset_collection
from utils.file_loader import extract_text_from_file
from utils.web_loader import extract_text_from_url
from schemas.response_models import IngestResponse

router = APIRouter()

def sync_extract_webpage(url: str) -> str:
    """Run the async extractor in a fresh event loop (needed for Playwright on Windows)."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    from document_ingestion.extractors import extract_webpage
    return asyncio.run(extract_webpage(url))


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    source_type: Optional[str] = Form(None),
    user_id: int = Depends(get_current_user),
):
    """
    Ingest a document by file upload or URL.
    Runs: text extraction → preprocessing → chunking → embedding → store.
    """
    if file is None and url is None:
        raise HTTPException(status_code=400, detail="Provide either a file or a URL.")

    # Step 1: Extract raw text
    try:
        if file is not None:
            # Save uploaded file to temp location
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name

            try:
                if source_type == 'audio':
                    from utils.file_loader import extract_text_from_audio
                    raw_text = extract_text_from_audio(tmp_path)
                elif source_type == 'simple_pdf':
                    from utils.file_loader import extract_text_from_pdf
                    raw_text = extract_text_from_pdf(tmp_path)
                elif source_type == 'ocr_pdf':
                    from utils.file_loader import extract_text_from_ocr_pdf
                    raw_text = extract_text_from_ocr_pdf(tmp_path)
                elif source_type == 'txt':
                    from utils.file_loader import extract_text_from_txt
                    raw_text = extract_text_from_txt(tmp_path)
                else:
                    raw_text = extract_text_from_file(tmp_path, file.filename)
            finally:
                os.unlink(tmp_path)
        else:
            if source_type == 'youtube':
                from utils.web_loader import extract_text_from_youtube
                raw_text = extract_text_from_youtube(url)
            elif source_type == 'website':
                # Use to_thread to run in a fresh loop via asyncio.run
                raw_text = await asyncio.to_thread(sync_extract_webpage, url)
            else:
                from utils.web_loader import extract_text_from_url
                raw_text = await extract_text_from_url(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract text: {str(e)}")

    if not raw_text or len(raw_text.strip()) < 10:
        raise HTTPException(status_code=422, detail="Could not extract meaningful text from the input.")

    # Step 2: Preprocess
    clean_text = process_text_to_markdown(raw_text)

    # Step 3: Chunk
    chunks = chunk_text(clean_text)

    if not chunks:
        raise HTTPException(status_code=422, detail="No chunks generated from the text.")

    # Step 4: Store embeddings persistently
    num_stored = store_chunks(chunks, user_id)

    return IngestResponse(
        status="success",
        message=f"Ingested and stored {num_stored} chunks.",
        num_chunks=num_stored,
    )
