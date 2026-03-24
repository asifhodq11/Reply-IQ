"""
app/services/usage_service.py

Tracks and enforces monthly reply limits based on the user's plan.
Free = 5 replies/month
Starter = 50 replies/month
"""

from datetime import datetime, timedelta

from app.extensions import supabase
from app.utils.exceptions import ReplyLimitReached


def get_plan_limit(plan: str) -> int:
    """Returns the monthly limit for a given plan."""
    if plan == "starter":
        return 50
    elif plan in ("growth", "pro"):
        return 999999
    return 5  # Free plan default


def check_usage_limit(user_id: str) -> None:
    """
    Reads live count from DB on every call.
    Prevents stale session cache from allowing
    over-limit requests when two arrive simultaneously.
    """
    result = (
        supabase.from_("users")
        .select("reply_count_this_month, plan, billing_cycle_start")
        .eq("id", user_id)
        .single()
        .execute()
    )
    user = result.data
    plan = user.get("plan", "free")
    used = user.get("reply_count_this_month", 0)
    limit = get_plan_limit(plan)

    billing_start_str = user.get("billing_cycle_start")
    if billing_start_str:
        billing_start = datetime.fromisoformat(billing_start_str)
        reset_date = billing_start + timedelta(days=30)
    else:
        reset_date = datetime.utcnow() + timedelta(days=30)

    if used >= limit:
        raise ReplyLimitReached(
            used=used,
            limit=limit,
            reset_date=reset_date.isoformat(),
        )


def increment_usage(user_id: str) -> None:
    """
    Increments the reply_count_this_month for the user by 1.
    Uses atomic RPC to prevent race conditions.
    """
    supabase.rpc("increment_reply_count", {"user_id_input": user_id}).execute()
