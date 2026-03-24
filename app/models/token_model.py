"""
app/models/token_model.py

Manages approval tokens for review replies.
Enforces atomic consumption to prevent double-processing.
"""

import secrets
from datetime import datetime, timedelta

from app.extensions import supabase
from app.utils.exceptions import TokenAlreadyUsed


def create_token(reply_id: str, user_id: str) -> str:
    """
    Generates a secure 32-byte URL-safe token.
    Sets expires_at to 24 hours from now.
    Inserts a row into the approval_tokens table.
    Returns the token string.
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    expires_at_iso = expires_at.isoformat() + "Z"

    supabase.from_("approval_tokens").insert(
        {"reply_id": reply_id, "user_id": user_id, "token": token, "expires_at": expires_at_iso, "used": False}
    ).execute()

    return token


def get_token(token_string: str) -> dict:
    """
    Queries the approval_tokens table by token string.
    Returns the row dict or None if not found.
    """
    result = supabase.from_("approval_tokens").select("*").eq("token", token_string).execute()

    return result.data[0] if result.data else None


def consume_token(token_string: str) -> bool:
    """
    Atomically consumes a token.
    UPDATE approval_tokens SET used=true WHERE token=token AND used=false
    Raises TokenAlreadyUsed() if 0 rows are updated.
    Returns True on success.
    """
    result = (
        supabase.from_("approval_tokens").update({"used": True}).eq("token", token_string).eq("used", False).execute()
    )

    if not result.data:
        raise TokenAlreadyUsed()

    return True


def get_reply_for_token(token_string: str) -> dict:
    """
    Joins approval_tokens with the replies table and returns
    the associated reply row, or None if not found.
    """
    result = supabase.from_("approval_tokens").select("*, replies(*)").eq("token", token_string).execute()

    if result.data and "replies" in result.data[0]:
        return result.data[0]["replies"]

    return None
