"""
app/services/stripe_service.py

Stripe integration: checkout, portal, webhook handling, cancellation.
Security rules enforced here:
  - Signature verified BEFORE any data is read from event
  - Webhook idempotency via processed_events in-memory set (replace with
    DB-backed check in Phase 9 hardening)
"""

import os
import stripe

from app.extensions import supabase
from app.utils.exceptions import StripeWebhookInvalid, ReplyIQError

# Set Stripe secret key on module import
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

# ── Idempotency guard ─────────────────────────────────────────
# Keeps track of Stripe event IDs already processed this process
# lifetime. Prevents duplicate plan changes on replay.
_processed_event_ids: set[str] = set()


# ── Function 1: create_checkout_session ──────────────────────


def create_checkout_session(user_id: str, user_email: str, plan: str) -> str:
    """
    Creates a Stripe Checkout session for the starter plan.
    Returns the session URL to redirect the user to.
    Raises ReplyIQError(SERVER_ERROR) if the Stripe call fails.
    """
    frontend_url = os.environ["FRONTEND_URL"]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[
                {
                    "price": os.environ["STRIPE_PRICE_ID_STARTER"],
                    "quantity": 1,
                }
            ],
            client_reference_id=user_id,
            customer_email=user_email,
            success_url=f"{frontend_url}/dashboard?payment=success",
            cancel_url=f"{frontend_url}/pricing?payment=cancelled",
        )
        return session.url
    except stripe.error.StripeError as e:
        from app.utils.logger import log_event

        log_event("stripe_api_error", error=str(e))
        raise ReplyIQError()


# ── Function 2: create_portal_session ────────────────────────


def create_portal_session(stripe_customer_id: str) -> str:
    """
    Creates a Stripe Billing Portal session for managing subscriptions.
    Returns the portal session URL.
    Raises ReplyIQError(SERVER_ERROR) if the Stripe call fails.
    """
    frontend_url = os.environ["FRONTEND_URL"]

    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=f"{frontend_url}/dashboard",
        )
        return session.url
    except stripe.error.StripeError as e:
        from app.utils.logger import log_event

        log_event("stripe_api_error", error=str(e))
        raise ReplyIQError()


# ── Function 3: handle_webhook_event ─────────────────────────


def handle_webhook_event(payload_bytes: bytes, sig_header: str) -> dict:
    """
    Verifies the webhook signature and processes the Stripe event.
    SECURITY: Signature is verified BEFORE reading any event data.
    Idempotent: skips events already processed in this process lifetime.
    """
    webhook_secret = os.environ["STRIPE_WEBHOOK_SECRET"]

    # 1. Verify signature first — raises StripeWebhookInvalid on failure
    try:
        event = stripe.Webhook.construct_event(
            payload=payload_bytes,
            sig_header=sig_header,
            secret=webhook_secret,
        )
    except stripe.error.SignatureVerificationError:
        raise StripeWebhookInvalid()

    event_id = event["id"]
    event_type = event["type"]

    # 2. Idempotency check — skip already-processed events
    if event_id in _processed_event_ids:
        return {"received": True}

    # 3. Handle supported event types
    if event_type == "checkout.session.completed":
        session_data = event["data"]["object"]
        user_id = session_data.get("client_reference_id")
        customer_id = session_data.get("customer")

        if user_id and customer_id:
            supabase.from_("users").update(
                {
                    "plan": "starter",
                    "stripe_customer_id": customer_id,
                }
            ).eq("id", user_id).execute()

    elif event_type == "invoice.payment_failed":
        invoice_data = event["data"]["object"]
        customer_id = invoice_data.get("customer")

        if customer_id:
            supabase.from_("users").update(
                {
                    "plan": "free",
                }
            ).eq("stripe_customer_id", customer_id).execute()

    # 4. Mark event as processed
    _processed_event_ids.add(event_id)

    return {"received": True}


# ── Function 4: cancel_subscription ──────────────────────────


def cancel_subscription(
    user_id: str,
    stripe_customer_id: str,
    reason: str = None,
) -> bool:
    """
    Cancels the active Stripe subscription at period end.
    Updates the users table: plan='free', cancellation_reason=reason.
    Returns True on success.
    """
    # Retrieve the customer's active subscriptions
    subscriptions = stripe.Subscription.list(
        customer=stripe_customer_id,
        status="active",
        limit=1,
    )

    if subscriptions.data:
        subscription = subscriptions.data[0]
        stripe.Subscription.modify(
            subscription.id,
            cancel_at_period_end=True,
        )

    # Update the user record regardless — downgrade plan immediately
    supabase.from_("users").update(
        {
            "plan": "free",
            "cancellation_reason": reason,
        }
    ).eq("id", user_id).execute()

    return True
