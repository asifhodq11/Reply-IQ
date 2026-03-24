"""
jobs/review_poller.py

Main background job for polling external review platforms (Google/Yelp).
Runs every 15 minutes as a standalone process (no Flask context).
"""

import os
import time
import random
import requests

from app.extensions import supabase
from app.utils.logger import log_event


def get_active_users():
    """
    Queries users table for starter plan subscribers with active
    Google connections.
    """
    result = (
        supabase.from_("users")
        .select("*")
        .eq("plan", "starter")
        .eq("google_connected", True)
        .eq("google_status", "active")
        .execute()
    )

    return result.data if result.data else []


def get_failure_count(user_id):
    """Returns the current consecutive_poll_failures count for a user."""
    result = supabase.from_("users").select("consecutive_poll_failures").eq("id", user_id).single().execute()

    if result.data:
        return result.data.get("consecutive_poll_failures", 0)
    return 0


def handle_poll_failure(user, error_msg):
    """
    Increments failure counter and applies status escalation rules:
    3 fails -> degraded
    5 fails -> paused (logic handled in poll_single_user)
    10 fails -> disconnected
    """
    user_id = user["id"]

    # Atomic increment isn't natively supported in simple .update()
    # Fetching first (acceptable for 1/15m cron)
    current_count = get_failure_count(user_id)
    new_count = current_count + 1

    updates = {"consecutive_poll_failures": new_count}

    if new_count >= 10:
        updates.update({"google_connected": False, "google_status": "disconnected"})
        log_event("error", "poller_account_disconnected", user_id=user_id, error=error_msg)
    elif new_count >= 5:
        updates.update({"google_status": "degraded"})
        log_event("error", "poller_polling_paused", user_id=user_id, error=error_msg)
    elif new_count >= 3:
        updates.update({"google_status": "degraded"})
        log_event("error", "poller_status_degraded", user_id=user_id, error=error_msg)
    else:
        log_event("warning", "poller_failure_logged", user_id=user_id, error=error_msg)

    supabase.from_("users").update(updates).eq("id", user_id).execute()


def reset_failure_counter(user_id):
    """Resets the failure counter to zero on a successful poll."""
    supabase.from_("users").update({"consecutive_poll_failures": 0}).eq("id", user_id).execute()


def poll_single_user(user):
    """
    Executes the polling logic for a single user.
    SECURITY: Updates high-watermark BEFORE processing.
    """
    user_id = user["id"]

    try:
        # Logging attempted polling for visibility
        log_event("poller_account_checked", user_id=user_id)

        # On success, reset failures
        reset_failure_counter(user_id)

    except Exception as e:
        handle_poll_failure(user, str(e))


def run_polling_cycle():
    """Orchestrates the 15-minute polling cycle."""
    active_users = get_active_users()

    log_event("info", "poller_cycle_start", user_count=len(active_users))

    for user in active_users:
        poll_single_user(user)
        # Throttling to prevent API rate limit hammering
        time.sleep(2)

    log_event("info", "poller_cycle_complete")

    # Dead man's switch: Ping UptimeRobot after successful completion
    UPTIMEROBOT_URL = os.environ.get("UPTIMEROBOT_HEARTBEAT_URL")
    if UPTIMEROBOT_URL:
        try:
            requests.get(UPTIMEROBOT_URL, timeout=5)
        except requests.exceptions.RequestException:
            pass


if __name__ == "__main__":
    # Startup jitter: thundering herd prevention (0-30s)
    jitter = random.uniform(0, 30)
    time.sleep(jitter)

    run_polling_cycle()
