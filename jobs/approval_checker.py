"""
jobs/approval_checker.py

Finds draft replies older than 24 hours for Tier 2 users (Manual Edit)
and auto-posts them to the external platform.
"""

from datetime import datetime, timedelta, timezone

from app.extensions import supabase
from app.utils.logger import log_event


def get_pending_auto_posts():
    """
    Finds draft replies older than 24 hours for users in Tier 2.
    Tier 2 = Manual Edit (Auto-post after 24h if no action).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    cutoff_iso = cutoff.isoformat()

    # Query replies joined with users to filter by approval_tier
    # Using PostgREST embedding: replies(..., users(...))
    result = (
        supabase.from_("replies")
        .select("*, users!inner(*), reviews!inner(*)")
        .eq("status", "draft")
        .lt("created_at", cutoff_iso)
        .eq("users.approval_tier", 2)
        .eq("reviews.is_deleted", False)
        .execute()
    )

    return result.data if result.data else []


def auto_post_reply(reply):
    """
    Handles the auto-posting of a single reply.
    Includes duplicate check to prevent double-posting.
    """
    reply_id = reply["id"]
    user_id = reply["user_id"]
    review_id = reply["review_id"]

    # Duplicate prevention: check if a reply for this review is already posted
    existing = (
        supabase.from_("replies")
        .select("id")
        .eq("review_id", review_id)
        .in_("status", ["posted", "auto-posted"])
        .execute()
    )

    if existing.data:
        log_event("info", "auto_post_skipped_duplicate", user_id=user_id, review_id=review_id)
        return

    # Phase 8 Google API — wire up in production
    # (Placeholder)
    success = True  # Simulate success for stub

    if success:
        supabase.from_("replies").update({"status": "auto-posted"}).eq("id", reply_id).eq("user_id", user_id).execute()

        log_event("info", "reply_auto_posted", user_id=user_id, reply_id=reply_id)


def run_auto_post_cycle():
    """Executes the auto-post cycle."""
    pending = get_pending_auto_posts()

    log_event("info", "auto_post_cycle_start", count=len(pending))

    for reply in pending:
        try:
            auto_post_reply(reply)
        except Exception as e:
            # One failure should not stop the entire cycle
            log_event("error", "auto_post_failed", reply_id=reply.get("id"), error=str(e))

    log_event("info", "auto_post_cycle_complete")


if __name__ == "__main__":
    run_auto_post_cycle()
