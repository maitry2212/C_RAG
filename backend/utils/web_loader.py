"""
Web loader utilities.
Extracts text from URLs (web pages) and YouTube videos.
Logic from Notebook 1.
"""

import re


def extract_text_from_youtube(url: str) -> str:
    """Extract transcript from a YouTube video URL."""
    from youtube_transcript_api import YouTubeTranscriptApi

    # Extract video ID from URL
    video_id = url.replace("https://www.youtube.com/watch?v=", "")
    video_id = video_id.replace("https://youtu.be/", "")
    # Remove any extra query params
    video_id = video_id.split("&")[0]

    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch(video_id)
    text = " ".join([t.text for t in transcript])
    return text


async def extract_text_from_web(url: str) -> str:
    """
    Extract text from a web page using playwright for JS rendering/bot bypass
    and BeautifulSoup to clean HTML.
    """
    from bs4 import BeautifulSoup
    from playwright.async_api import async_playwright

    html_content = ""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            html_content = await page.content()
        finally:
            await browser.close()

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text


async def extract_text_from_url(url: str) -> str:
    """
    Route to the correct extractor based on URL type.
    Returns raw extracted text.
    """
    if "youtube.com" in url or "youtu.be" in url:
        return extract_text_from_youtube(url)
    else:
        return await extract_text_from_web(url)
