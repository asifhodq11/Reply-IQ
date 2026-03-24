"""
app/models/reply_model.py

Handles Supabase operations for the replies table.
All queries MUST include .eq('user_id', current_user_id) per Security Rule 1.
"""

from app.extensions import supabase
from app.utils.logger import log_event


def insert_reply(user_id: str, reply_data: dict) -> dict | None:
    """Inserts a new AI reply draft."""
    try:
        data_to_insert = {**reply_data, "user_id": user_id}
        result = supabase.table("replies").insert(data_to_insert).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        log_event("error", "insert_reply_failed", user_id=user_id, error=str(e))
        return None


def get_replies_by_review(user_id: str, review_id: str) -> list[dict]:
    """Fetches all replies for a specific review, strictly scoped to the owner."""
    try:
        result = supabase.table("replies").select("*").eq("review_id", review_id).eq("user_id", user_id).execute()
        return result.data if result.data else []
    except Exception as e:
        log_event("error", "get_replies_failed", user_id=user_id, review_id=review_id, error=str(e))
        return []
