"""
app/models/review_model.py

Handles Supabase operations for the reviews table.
All queries MUST include .eq('user_id', current_user_id) per Security Rule 1.
"""

from app.extensions import supabase
from app.utils.logger import log_event


def insert_review(user_id: str, review_data: dict) -> dict | None:
    """Inserts a new review and returns the created record."""
    try:
        data_to_insert = {**review_data, "user_id": user_id}
        result = supabase.table("reviews").insert(data_to_insert).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        log_event("error", "insert_review_failed", user_id=user_id, error=str(e))
        return None


def get_review_by_id(user_id: str, review_id: str) -> dict | None:
    """Fetches a single review by ID, strictly scoped to the owner."""
    try:
        result = (
            supabase.table("reviews")
            .select("*")
            .eq("id", review_id)
            .eq("user_id", user_id)
            .eq("is_deleted", False)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        log_event("error", "get_review_failed", user_id=user_id, review_id=review_id, error=str(e))
        return None


def update_review_status(user_id: str, review_id: str, status: str) -> bool:
    """Updates the status of a review record."""
    try:
        supabase.table("reviews").update({"status": status}).eq("id", review_id).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        log_event(
            "error", "update_review_status_failed", user_id=user_id, review_id=review_id, status=status, error=str(e)
        )
        return False
