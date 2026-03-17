"""
ReplyIQ — Environment Variable Verification
Run this to check all required env vars are set before starting the app.
Usage: python scripts/verify_env.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Every key the app needs to run — 14 total
REQUIRED_KEYS = [
    "FLASK_ENV",
    "SECRET_KEY",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PRICE_ID_STARTER",
    "RESEND_API_KEY",
    "FRONTEND_URL",
    "GOOGLE_API_KEY",
]

# Optional keys — app works without them but some features won't
OPTIONAL_KEYS = [
    "UPTIMEROBOT_HEARTBEAT_URL",
]


def verify():
    missing = []
    placeholder = []

    for key in REQUIRED_KEYS:
        value = os.environ.get(key, "")
        if not value:
            missing.append(key)
        elif value.startswith("your-") or value == "change-me-to-a-random-string":
            placeholder.append(key)

    # Report results
    print("=== ReplyIQ Environment Check ===\n")

    if not missing and not placeholder:
        print("All 14 required keys are set.")
        print("Status: READY\n")
        return True

    if missing:
        print(f"MISSING ({len(missing)}):")
        for key in missing:
            print(f"  - {key}")
        print()

    if placeholder:
        print(f"STILL PLACEHOLDER ({len(placeholder)}):")
        for key in placeholder:
            print(f"  - {key}  (currently: {os.environ.get(key, '')[:20]}...)")
        print()

    # Check optional keys
    for key in OPTIONAL_KEYS:
        value = os.environ.get(key, "")
        if not value:
            print(f"OPTIONAL (not set): {key}")

    print("\nStatus: NOT READY — fill in .env before running the app.")
    return False


if __name__ == "__main__":
    ok = verify()
    sys.exit(0 if ok else 1)
