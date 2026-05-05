"""
history.py — Persist and retrieve query history in NeonDB (PostgreSQL).

Replaces the old SQLite-based implementation.
"""

from typing import List, Dict
from core.database import get_connection


def save_query(
    chat_id: int,
    user_id: int,
    question: str,
    answer: str,
    verdict: str = None,
    reason: str = None,
) -> None:
    """Insert one Q&A record into the NeonDB history table."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO query_history (chat_id, user_id, question, answer, verdict, reason)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (chat_id, user_id, question, answer, verdict, reason),
            )
        conn.commit()
    finally:
        conn.close()


def get_history(user_id: int, limit: int = 20) -> List[Dict]:
    """Return the most recent *limit* Q&A records for a specific user from NeonDB."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT question, answer, verdict, reason, created_at AS timestamp
                FROM query_history
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cur.fetchall()
        # RealDictCursor already returns dict-like rows; cast for safety
        return [dict(row) for row in rows]
    finally:
        conn.close()
