"""
app/routes/approvals.py

Handles token-based approvals for generated review replies.
No authentication is required since the token itself serves as auth.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timezone

from app.models.token_model import get_token, consume_token, get_reply_for_token
from app.services.reply_poster import post_reply_to_google
from app.utils.exceptions import TokenInvalid, TokenExpired, TokenAlreadyUsed
from app.extensions import supabase

approvals_bp = Blueprint("approvals", __name__)


# ── ROUTE 1 — GET /api/v1/approve/{token} ────────────────────


@approvals_bp.route("/<token>", methods=["GET"])
def get_approval(token):
    """
    Validates a token and returns the associated reply for review.
    Raises errors if the token is invalid, used, or expired.
    """
    row = get_token(token)
    if not row:
        raise TokenInvalid()

    expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        raise TokenExpired()

    if row["used"]:
        raise TokenAlreadyUsed()

    reply = get_reply_for_token(token)
    if not reply or reply.get("is_deleted"):
        raise TokenInvalid()

    return (
        jsonify(
            {
                "token": token,
                "reply": reply,
            }
        ),
        200,
    )


# ── ROUTE 2 — POST /api/v1/approve/{token} ───────────────────


@approvals_bp.route("/<token>", methods=["POST"])
def post_approval(token):
    """
    Accepts an approval token.
    Atomically consumes it to prevent double-processing.
    Optionally accepts edited reply_text and updates the DB.
    Posts to the external platform (Google) and updates reply status.
    """
    row = get_token(token)
    if not row:
        raise TokenInvalid()

    expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        raise TokenExpired()

    if row["used"]:
        raise TokenAlreadyUsed()

    # Consumes token atomically (Raises TokenAlreadyUsed on race condition)
    consume_token(token)

    reply = get_reply_for_token(token)
    if not reply or reply.get("is_deleted"):
        raise TokenInvalid()

    data = request.get_json(silent=True) or {}
    new_text = data.get("reply_text")

    # If the user edited the text before approving, save it
    if new_text and new_text != reply["reply_text"]:
        supabase.from_("replies").update({"reply_text": new_text, "was_edited": True}).eq("id", reply["id"]).eq(
            "user_id", row["user_id"]
        ).execute()

    # Delegate to the poster service
    post_reply_to_google(reply["id"], row["user_id"])

    return jsonify({"status": "posted"}), 200
