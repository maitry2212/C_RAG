import sqlite3
import os
from typing import List, Dict
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chat_history.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            verdict TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_query(question: str, answer: str, verdict: str = None, reason: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (question, answer, verdict, reason)
        VALUES (?, ?, ?, ?)
    ''', (question, answer, verdict, reason))
    conn.commit()
    conn.close()

def get_history(limit: int = 20) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT question, answer, verdict, reason, timestamp
        FROM history
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# Initialize on import
init_db()
