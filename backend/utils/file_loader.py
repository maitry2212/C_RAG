"""
File loader utilities.
Extracts text from various file types: PDF, TXT, OCR PDF, audio.
Logic from Notebook 1.
"""

import os
import tempfile
from typing import Optional


def extract_text_from_pdf(file_path: str) -> str:
    """Extract markdown text from a regular PDF using pymupdf4llm."""
    import pymupdf4llm
    md_text = pymupdf4llm.to_markdown(file_path)
    return md_text


def extract_text_from_txt(file_path: str) -> str:
    """Read plain text from a .txt file."""
    with open(file_path) as f:
        data = f.read()
    return data


def extract_text_from_ocr_pdf(file_path: str) -> str:
    """Extract text from scanned/OCR PDF using docling."""
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()


def extract_text_from_audio(file_path: str) -> str:
    """Transcribe audio file using Groq Whisper."""
    from groq import Groq
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)

    with open(file_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=file,
            model="whisper-large-v3"
        )

    return transcription.text


def extract_text_from_file(file_path: str, filename: str) -> str:
    """
    Route to the correct extractor based on file extension.
    Returns raw extracted text.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".txt":
        return extract_text_from_txt(file_path)
    elif ext == ".pdf":
        # Try regular PDF first; if it returns very little text, use OCR
        text = extract_text_from_pdf(file_path)
        if len(text.strip()) < 50:
            text = extract_text_from_ocr_pdf(file_path)
        return text
    elif ext in (".mp3", ".wav", ".m4a", ".ogg", ".flac"):
        return extract_text_from_audio(file_path)
    else:
        # Fallback: try reading as plain text
        return extract_text_from_txt(file_path)
