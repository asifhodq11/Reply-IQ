"""
app/routes/reviews.py

REST API endpoint for submitting manual reviews and orchestrating
the AI Engine pipeline.
"""

import time
from flask import Blueprint, g, jsonify, request
from app.schemas.review_schema import GenerateReplySchema

from app.utils.decorators import require_auth, validate_request
from app.utils.errors import build_error
from app.utils.logger import log_event
from app.extensions import supabase, limiter

from app.models.review_model import insert_review
from app.models.reply_model import insert_reply

from app.services.usage_service import check_usage_limit, increment_usage
from app.services.model_router import classify_complexity, get_model_for_complexity
from app.services.ai_engine import generate_reply


reviews_bp = Blueprint("reviews", __name__)




@reviews_bp.route("/generate", methods=["POST"])
@require_auth
@limiter.limit("20 per hour")
@validate_request(GenerateReplySchema)
def generate():
    """
    Submits a review and generates a 3-pass AI reply.
    """
    user = g.current_user
    data = g.validated_data
    user_id = user["id"]

    # 1. Enforce Subscription Usage Limits
    check_usage_limit(user_id)

    # 2. Save the incoming review to DB
    review_data = {
        "star_rating": data["rating"],
        "review_text": data["review_text"] if data["review_text"] else None,
        "reviewer_name": data["reviewer_name"] if data["reviewer_name"] else None,
        "google_review_id": data["google_review_id"],
        "status": "pending",
    }

    saved_review = insert_review(user_id, review_data)
    if not saved_review:
        return build_error("SERVER_ERROR", details="Failed to persist review.")

    # 3. Generate the AI Reply
    log_event("ai_generation_start", user_id=user_id, review_id=saved_review["id"])
    start_time = time.time()

    reply_text = generate_reply(
        business_name=user.get("business_name", "your business"),
        business_type=user.get("business_type", "business"),
        tone_preference=user.get("tone_preference", "friendly"),
        star_rating=data["rating"],
        review_text=data.get("review_text", ""),
    )

    duration_ms = int((time.time() - start_time) * 1000)

    # Track which model was chosen
    complexity = classify_complexity(data["rating"], data.get("review_text", ""))
    model_used = get_model_for_complexity(complexity)

    # 4. Save the generated reply to DB
    reply_data = {
        "review_id": saved_review["id"],
        "reply_text": reply_text,
        "status": "draft",
        "generation_ms": duration_ms,
        "model_used": model_used,
    }

    saved_reply = insert_reply(user_id, reply_data)
    if not saved_reply:
        return build_error("SERVER_ERROR", details="Reply generation succeeded but failed to save to database.")

    # 5. Mark review as 'replied' now that reply is saved
    from app.models.review_model import update_review_status

    update_review_status(user_id, saved_review["id"], "replied")

    # 6. Increment Usage atomically via RPC
    try:
        increment_usage(user_id)
    except Exception as e:
        log_event("increment_usage_failed", user_id=user_id, level="error", error=str(e))
        # We don't fail the request here, but we log the usage drift.

    log_event("ai_generation_success", user_id=user_id, review_id=saved_review["id"], ms=duration_ms)

    # Standard success
    return jsonify({"review": saved_review, "reply": saved_reply}), 201


@reviews_bp.route("/history", methods=["GET"])
@require_auth
def history():
    """
    Returns a paginated list of reviews (with reply status) for the current user.
    Soft-deleted reviews (is_deleted=true) are never returned.
    """
    user_id = g.current_user["id"]

    # Parse and clamp pagination params
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except (ValueError, TypeError):
        per_page = 20

    offset = (page - 1) * per_page

    # Fetch total count (non-deleted, this user only)
    count_result = (
        supabase.from_("reviews").select("id", count="exact").eq("user_id", user_id).eq("is_deleted", False).execute()
    )
    total = count_result.count if count_result.count is not None else 0

    # Fetch page of reviews
    rows_result = (
        supabase.from_("reviews")
        .select("id, review_text, star_rating, reviewer_name, platform, status, created_at")
        .eq("user_id", user_id)
        .eq("is_deleted", False)
        .order("created_at", desc=True)
        .range(offset, offset + per_page - 1)
        .execute()
    )

    items = rows_result.data or []
    has_more = (offset + len(items)) < total

    return (
        jsonify(
            {
                "items": items,
                "total": total,
                "has_more": has_more,
            }
        ),
        200,
    )
