"""
database.py — NeonDB (PostgreSQL) connection and table initialisation.

Uses DATABASE_URL from .env via python-dotenv.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add it to your .env file."
    )


def get_connection():
    """Return a new psycopg2 connection to NeonDB."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db() -> None:
    """
    Create all required tables if they do not already exist.
    Call this once at application startup.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # ── Disable this drop in production! ──────────────────────────
            # Only doing this to easily roll out our new schema during dev
            # cur.execute("DROP TABLE IF EXISTS query_history, chats, users CASCADE;")

            # ── Users ─────────────────────────────────────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            SERIAL PRIMARY KEY,
                    name          TEXT        NOT NULL,
                    email         TEXT        NOT NULL UNIQUE,
                    password_hash TEXT        NOT NULL,
                    created_at    TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            # ── Chats ─────────────────────────────────────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id          SERIAL PRIMARY KEY,
                    user_id     INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title       TEXT        NOT NULL,
                    created_at  TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            # ── Query / chat history ──────────────────────────────────────
            # To avoid dropping, if altering is needed later we alter. For now we assume new or wiped Neon DB or we can manually migrate.
            # Using IF NOT EXISTS. If it exists but lacks columns, it will fail later unless we drop or alter.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS query_history (
                    id          SERIAL PRIMARY KEY,
                    chat_id     INTEGER     NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                    user_id     INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    question    TEXT        NOT NULL,
                    answer      TEXT        NOT NULL,
                    verdict     TEXT,
                    reason      TEXT,
                    created_at  TIMESTAMPTZ DEFAULT NOW()
                );
            """)

        conn.commit()
        print("[DB] Tables verified / created on NeonDB OK")
    finally:
        conn.close()
