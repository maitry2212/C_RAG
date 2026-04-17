"""
Text preprocessing service.
Logic from Notebook 2 — process_text_to_markdown function.
"""

import re


def process_text_to_markdown(text: str) -> str:
    """
    Convert raw text / markdown to clean markdown for RAG.
    Exact logic from Notebook 2.
    """

    # 1️⃣ Remove markdown links but keep the text
    # [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)

    # 2️⃣ Remove raw URLs
    text = re.sub(r'http\S+|www\S+', '', text)

    # 3️⃣ Remove navigation / junk words
    junk_patterns = [
        r'Log in',
        r'Get started',
        r'Sign up',
        r'More information',
        r'Found an Error\?',
        r'English|Español|Português|Deutsch|Français',
    ]

    for pattern in junk_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # 4️⃣ Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)

    # remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 5️⃣ Preserve headings (ensure spacing before headings)
    text = re.sub(r'\n(#)', r'\n\n\1', text)

    # strip start/end spaces
    text = text.strip()

    return text
