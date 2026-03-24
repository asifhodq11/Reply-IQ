"""
app/services/gdpr_service.py

GDPR-compliant account deletion (anonymisation).
Called by DELETE /api/v1/auth/account.

Rules:
- No Flask imports. No create_app(). Plain function only.
- Anonymises users, reviews, and replies tables in order.
- Never hard-deletes — marks the account as deleted and strips PII.
"""

from app.extensions import supabase
from app.utils.logger import log_event


def anonymise_user(user_id: str) -> None:
    """
    Anonymises all PII for the given user_id across three tables.

    Step order:
      1. Anonymise users row (email, business_name, stripe ID, etc.)
      2. Null review PII (review_text, reviewer_name)
      3. Anonymise reply text
      4. Log the event
    """

    # ── Step 1: Anonymise the users table row ─────────────────────
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

    # ── Step 2: Null review PII for this user ─────────────────────
    supabase.from_("reviews").update(
        {
            "review_text": None,
            "reviewer_name": None,
        }
    ).eq("user_id", user_id).execute()

    # ── Step 3: Anonymise replies for this user ───────────────────
    supabase.from_("replies").update(
        {
            "reply_text": "[Deleted]",
        }
    ).eq("user_id", user_id).execute()

    # ── Step 4: Log event ─────────────────────────────────────────
    log_event("account_anonymised", user_id=user_id)
