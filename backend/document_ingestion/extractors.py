# document_ingestion/extractors.py
import os
import asyncio
from typing import Optional

import pymupdf4llm
from docling.document_converter import DocumentConverter
from crawl4ai import AsyncWebCrawler
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi

from .utils import clean_text, to_markdown

def extract_pdf_pymupdf(file_path: str) -> str:
    """
    Uses pymupdf4llm to extract Markdown from a PDF.
    
    Args:
        file_path (str): The logical path to the PDF file.
        
    Returns:
        str: The extracted Markdown text, cleaned and ready for RAG.
    """
    md_text = pymupdf4llm.to_markdown(file_path)
    return clean_text(md_text)

def extract_pdf_docling(file_path: str) -> str:
    """
    Uses docling for OCR PDFs and returns Markdown.
    
    Args:
        file_path (str): The path to the OCR PDF file.
        
    Returns:
        str: The extracted Markdown text, cleaned and ready for RAG.
    """
    converter = DocumentConverter()
    result = converter.convert(file_path)
    md_text = result.document.export_to_markdown()
    
    return clean_text(md_text)

def extract_txt(file_path: str) -> str:
    """
    Reads a .txt file and converts it into Markdown text.
    
    Args:
        file_path (str): The path to the text file.
        
    Returns:
        str: The content formatted as a Markdown string.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    cleaned_txt = clean_text(text)
    title = os.path.basename(file_path)
    
    return to_markdown(title, cleaned_txt)

import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup

async def extract_webpage(url: str) -> str:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url
        )

        html = result.html  
        soup = BeautifulSoup(html, "lxml")

        title = soup.title.text if soup.title else None

        author = soup.find("meta", {"name": "author"})
        author = author["content"] if author else None

        description = soup.find("meta", {"name": "description"})
        description = description["content"] if description else None

        # Use crawl4ai's built-in markdown extraction for full content,
        # instead of relying on the <article> tag which is incomplete on this page.
        content = result.markdown

        data = {
            "title": title,
            "author": author,
            "description": description,
            "content": content,
            "url": result.url
        }
        print("**************************************")
        print(data)
        print("******************************************")
        print(f'data length: {len(data)}')
        print(f'title length: {len(data["title"])}')
        #print(f'author length: {len(data["author"])}')
        #print(f'description length: {len(data["description"])}')
        print(f'content length: {len(data["content"])}')
        print("******************************************")
    return content


def extract_audio(file_path: str) -> str:
    """
    Uses Whisper (via Groq) to transcribe audio and return Markdown transcript.
    
    Args:
        file_path (str): The path to the audio file.
        
    Returns:
        str: The transcribed text formatted as Markdown.
    """
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    
    with open(file_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=file,
            model="whisper-large-v3"
        )
        
    cleaned_txt = clean_text(transcription.text)
    title = os.path.basename(file_path)
    
    return to_markdown(title, cleaned_txt)

def extract_youtube(video_url: str) -> str:
    """
    Uses youtube-transcript-api to retrieve transcript and convert it into Markdown.
    
    Args:
        video_url (str): The URL of the YouTube video.
        
    Returns:
        str: The transcript formatted as Markdown.
    """
    if "v=" in video_url:
        video_id = video_url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in video_url:
        video_id = video_url.split("youtu.be/")[1].split("?")[0]
    else:
        video_id = video_url.replace("https://www.youtube.com/watch?v=", "")

    # Retrieve the transcript via youtube_transcript_api
    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
    text = " ".join([entry["text"] for entry in transcript_data])
            
    cleaned_txt = clean_text(text)
    title = f"YouTube Transcript: {video_id}"
    
    return to_markdown(title, cleaned_txt)
