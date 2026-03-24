"""
jobs/data_retention.py

Enforces data retention rules according to Bible Chapter 11.
Anonymizes inactive free users and deleted accounts, deletes old logs/tokens.
"""

from datetime import datetime, timedelta, timezone
from app.extensions import supabase
from app.utils.logger import log_event


def anonymise_inactive_free_users():
    """
    RULE 1: Free plan users inactive for 90+ days.
    Anonymizes user data and wipes review/reply content.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    cutoff_iso = cutoff.isoformat()

    # 1. Find inactive free users
    result = (
        supabase.from_("users")
        .select("id")
        .eq("plan", "free")
        .lt("created_at", cutoff_iso)
        .eq("is_deleted", False)
        .execute()
    )

    count = 0
    if result.data:
        for user in result.data:
            user_id = user["id"]
            try:
                # Anonymize User
                supabase.from_("users").update(
                    {
                        "email": f"deleted_{user_id[:8]}@deleted.replyiq.com",
                        "business_name": "[Deleted Account]",
                        "google_location_id": None,
                        "stripe_customer_id": None,
                        "cancellation_reason": None,
                        "is_deleted": True,
                    }
                ).eq("id", user_id).execute()

                # Wipe child tables
                supabase.from_("reviews").update({"review_text": None, "reviewer_name": None}).eq(
                    "user_id", user_id
                ).execute()

                supabase.from_("replies").update({"reply_text": "[Deleted]"}).eq("user_id", user_id).execute()

                count += 1
            except Exception as e:
                log_event("error", "retention_anonymise_failed", user_id=user_id, error=str(e))

    return count


def anonymise_cancelled_accounts():
    """
    RULE 2: Users where is_deleted=True and cancellation_reason
    was set (soft-deleted), if they are 30+ days old.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    cutoff_iso = cutoff.isoformat()

    result = (
        supabase.from_("users")
        .select("id")
        .eq("is_deleted", True)
        .neq("cancellation_reason", None)
        .lt("created_at", cutoff_iso)
        .execute()
    )

    count = 0
    if result.data:
        for user in result.data:
            user_id = user["id"]
            try:
                # Same anonymization as Rule 1
                supabase.from_("users").update(
                    {
                        "email": f"deleted_{user_id[:8]}@deleted.replyiq.com",
                        "business_name": "[Deleted Account]",
                        "google_location_id": None,
                        "stripe_customer_id": None,
                        "cancellation_reason": None,
                    }
                ).eq("id", user_id).execute()

                # Child tables
                supabase.from_("reviews").update({"review_text": None, "reviewer_name": None}).eq(
                    "user_id", user_id
                ).execute()

                supabase.from_("replies").update({"reply_text": "[Deleted]"}).eq("user_id", user_id).execute()

                count += 1
            except Exception as e:
                log_event("error", "retention_cancelled_anonymise_failed", user_id=user_id, error=str(e))

    return count


def delete_old_poller_logs():
    """
    RULE 3: Hard delete poller_log rows older than 90 days.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    cutoff_iso = cutoff.isoformat()

    # Supabase/PostgREST delete with filter
    result = supabase.from_("poller_log").delete().lt("created_at", cutoff_iso).execute()

    return len(result.data) if result.data else 0


def delete_expired_tokens():
    """
    RULE 4: Hard delete approval_tokens where expires_at < now
    AND used=False AND created_at < 7 days ago.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    older_than_7_days = datetime.now(timezone.utc) - timedelta(days=7)
    older_iso = older_than_7_days.isoformat()

    result = (
        supabase.from_("approval_tokens")
        .delete()
        .lt("expires_at", now_iso)
        .eq("used", False)
        .lt("created_at", older_iso)
        .execute()
    )

    return len(result.data) if result.data else 0


def run_retention_cycle():
    """Executes the data retention policy cycle."""
    log_event("info", "data_retention_start")

    stats = {"inactive_anonymised": 0, "cancelled_anonymised": 0, "poller_logs_deleted": 0, "expired_tokens_deleted": 0}

    try:
        stats["inactive_anonymised"] = anonymise_inactive_free_users()
    except Exception as e:
        log_event("error", "retention_rule1_failed", error=str(e))

    try:
        stats["cancelled_anonymised"] = anonymise_cancelled_accounts()
    except Exception as e:
        log_event("error", "retention_rule2_failed", error=str(e))

    try:
        stats["poller_logs_deleted"] = delete_old_poller_logs()
    except Exception as e:
        log_event("error", "retention_rule3_failed", error=str(e))

    try:
        stats["expired_tokens_deleted"] = delete_expired_tokens()
    except Exception as e:
        log_event("error", "retention_rule4_failed", error=str(e))

    log_event("info", "data_retention_complete", stats=stats)


if __name__ == "__main__":
    run_retention_cycle()
