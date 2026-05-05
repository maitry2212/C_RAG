from fastapi import APIRouter, Depends, HTTPException
from core.database import get_connection
from api.auth import get_current_user
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ChatCreateReq(BaseModel):
    title: str

@router.post("/")
def create_chat(req: ChatCreateReq, user_id: int = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chats (user_id, title) VALUES (%s, %s) RETURNING id, title, created_at",
                (user_id, req.title)
            )
            chat = cur.fetchone()
            conn.commit()
            return chat
    finally:
        conn.close()

@router.get("/")
def list_chats(user_id: int = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, created_at FROM chats WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            return cur.fetchall()
    finally:
        conn.close()

@router.delete("/{chat_id}")
def delete_chat(chat_id: int, user_id: int = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chats WHERE id = %s AND user_id = %s RETURNING id", (chat_id, user_id))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Chat not found or unauthorized")
            conn.commit()
            return {"status": "deleted"}
    finally:
        conn.close()

@router.get("/{chat_id}/history")
def get_chat_history(chat_id: int, user_id: int = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Verify ownership
            cur.execute("SELECT id FROM chats WHERE id = %s AND user_id = %s", (chat_id, user_id))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Chat not found or unauthorized")
            
            cur.execute("""
                SELECT question, answer, verdict, reason, created_at AS timestamp
                FROM query_history
                WHERE chat_id = %s
                ORDER BY created_at ASC
            """, (chat_id,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()
