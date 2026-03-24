"""
app/routes/payments.py

POST /checkout  → create Stripe checkout session
POST /webhook   → handle Stripe webhook events (raw bytes, signature verified first)
GET  /portal    → create Stripe billing portal session
POST /cancel    → cancel subscription at period end
"""

from flask import Blueprint, g, jsonify, request

from app.utils.decorators import require_auth
from app.utils.exceptions import StripeWebhookInvalid, ValidationError, ReplyNotFound
from app.services import stripe_service


payments_bp = Blueprint("payments", __name__)


# ── ROUTE 1 — POST /checkout ──────────────────────────────────


@payments_bp.route("/checkout", methods=["POST"])
@require_auth
def checkout():
    """
    Creates a Stripe Checkout session for the starter plan.
    Returns the checkout URL to redirect the user to.
    """
    user = g.current_user
    data = request.json or {}
    plan = data.get("plan")

    if plan != "starter":
        raise ValidationError(
            fields={"plan": ['Must be "starter".']},
            message="Invalid plan value.",
        )

    url = stripe_service.create_checkout_session(
        user_id=user["id"],
        user_email=user["email"],
        plan=plan,
    )

    return jsonify({"checkout_url": url}), 200


# ── ROUTE 2 — POST /webhook ───────────────────────────────────


@payments_bp.route("/webhook", methods=["POST"])
def webhook():
    """
    Receives Stripe webhook events.
    CRITICAL: reads raw bytes — NEVER request.json.
    Signature is verified before any event data is read.
    """
    payload_bytes = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    if not sig_header:
        raise StripeWebhookInvalid()

    result = stripe_service.handle_webhook_event(payload_bytes, sig_header)
    return jsonify(result), 200


# ── ROUTE 3 — GET /portal ─────────────────────────────────────


@payments_bp.route("/portal", methods=["GET"])
@require_auth
def portal():
    """
    Creates a Stripe Billing Portal session for the current user.
    Requires the user to already have a stripe_customer_id.
    """
    user = g.current_user
    stripe_customer_id = user.get("stripe_customer_id")

    if not stripe_customer_id:
        raise ReplyNotFound()

    url = stripe_service.create_portal_session(stripe_customer_id)
    return jsonify({"portal_url": url}), 200


# ── ROUTE 4 — POST /cancel ────────────────────────────────────


@payments_bp.route("/cancel", methods=["POST"])
@require_auth
def cancel():
    """
    Cancels the user's Stripe subscription at period end.
    Optionally accepts a cancellation reason in the request body.
    """
    user = g.current_user
    data = request.json or {}
    reason = data.get("reason")
    stripe_customer_id = user.get("stripe_customer_id")

    stripe_service.cancel_subscription(
        user_id=user["id"],
        stripe_customer_id=stripe_customer_id,
        reason=reason,
    )

    return jsonify({"status": "cancelled"}), 200
