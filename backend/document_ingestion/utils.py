# document_ingestion/utils.py
import re
from typing import List
from datetime import datetime
from langchain_core.documents import Document

def clean_text(text: str) -> str:
    """
    Cleans the given text to prepare it for RAG processing.
    
    Responsibilities:
    - Removes URLs
    - Removes Markdown links
    - Removes repeated whitespace
    - Normalizes line breaks
    - Removes navigation artifacts
    
    Args:
        text (str): The raw text to be cleaned.
        
    Returns:
        str: The cleaned text.
    """
    if not text:
        return ""
    
    # Remove Markdown links like [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove standalone URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove common navigation artifacts
    nav_artifacts = r'(?i)\b(skip to content|menu|home|about us|contact|login|sign in|navigation)\b'
    text = re.sub(nav_artifacts, '', text)
    
    # Normalize line breaks (convert 3 or more newlines into exactly 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove repeated whitespace within lines
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    return text.strip()

def to_markdown(title: str, text: str) -> str:
    """
    Formats the given text into Markdown format with a title.
    
    Args:
        title (str): The title to use for the Markdown document.
        text (str): The text content to format.
        
    Returns:
        str: The formatted Markdown string.
    """
    return f"# {title}\n\n{text}"

def text_to_documents(text: str, source: str, doc_type: str) -> List[Document]:
    """
    Converts plain text into a LangChain Document with metadata.
    
    Args:
        text (str): The text content of the document.
        source (str): The source of the document (e.g., file path or URL).
        doc_type (str): The type of the document (e.g., 'pdf', 'txt', 'audio').
        
    Returns:
        List[Document]: A list containing the created Document object.
    """
    metadata = {
        "source": source,
        "type": doc_type,
        "ingestion_time": datetime.utcnow().isoformat()
    }
    
    return [Document(page_content=text, metadata=metadata)]

