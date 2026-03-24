"""
tests/integration/test_smoke.py

8 end-to-end smoke tests.
All external services (Supabase, OpenAI, Gemini, Stripe) are mocked.
Tests verify that routes, services, and models wire together correctly.
"""

import os

# Set dummy env vars BEFORE any app imports
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")

FAKE_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSJ9.fake"
os.environ.setdefault("SUPABASE_ANON_KEY", FAKE_JWT)
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", FAKE_JWT)
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")
os.environ.setdefault("STRIPE_SECRET_KEY", "test-stripe-key")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "test-webhook-secret")
os.environ.setdefault("STRIPE_PRICE_ID_STARTER", "test-price-id")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("FRONTEND_URL", "http://test.localhost")

import pytest
from unittest.mock import MagicMock, patch

# Mock supabase.create_client BEFORE importing the app to avoid "Invalid API key" errors
# during module-level initialization in app/extensions.py
with patch("supabase.create_client") as mock_create:
    mock_create.return_value = MagicMock()
    from app import create_app


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────

FAKE_USER_ID = "bbbbbbbb-1111-1111-1111-bbbbbbbbbbbb"
FAKE_REVIEW_ID = "rrrrrrrr-1111-1111-1111-rrrrrrrrrrrr"
FAKE_REPLY_ID = "pppppppp-1111-1111-1111-pppppppppppp"

FAKE_USER_ROW = {
    "id": FAKE_USER_ID,
    "email": "smoke@example.com",
    "business_name": "Smoke Cafe",
    "business_type": "restaurant",
    "tone_preference": "friendly",
    "plan": "free",
    "reply_count_this_month": 0,
    "billing_cycle_start": "2026-03-01",
    "approval_tier": 2,
    "google_connected": False,
    "google_status": "none",
    "google_location_id": None,
    "stripe_customer_id": None,
    "consecutive_poll_failures": 0,
    "cancellation_reason": None,
    "time_to_first_value_ms": None,
    "is_deleted": False,
    "created_at": "2026-03-01T00:00:00Z",
}

FAKE_REVIEW_ROW = {
    "id": FAKE_REVIEW_ID,
    "user_id": FAKE_USER_ID,
    "star_rating": 4,
    "review_text": "Great service, will return.",
    "reviewer_name": "John",
    "status": "pending",
    "is_deleted": False,
}

FAKE_REPLY_ROW = {
    "id": FAKE_REPLY_ID,
    "user_id": FAKE_USER_ID,
    "review_id": FAKE_REVIEW_ID,
    "reply_text": "Thank you for visiting Smoke Cafe!",
    "status": "draft",
    "generation_ms": 800,
    "model_used": "gpt-4o-mini",
}


@pytest.fixture()
def app():
    application = create_app("testing")
    application.config["TESTING"] = True
    application.config["FORCE_HTTPS"] = False
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


def _make_auth_response(user_id=FAKE_USER_ID):
    """Fake Supabase auth response with session."""
    mock_user = MagicMock()
    mock_user.id = user_id

    mock_session = MagicMock()
    mock_session.access_token = "smoke.fake.jwt"

    mock_response = MagicMock()
    mock_response.user = mock_user
    mock_response.session = mock_session
    return mock_response


def _authed_client(client):
    """Set the session_token cookie so require_auth passes."""
    client.set_cookie("session_token", "smoke.fake.jwt")
    return client


def _mock_decorator_auth(mock_sb):
    """Wire the decorator-level auth mock to return FAKE_USER_ROW."""
    mock_user_resp = MagicMock()
    mock_user_resp.user = MagicMock(id=FAKE_USER_ID)
    mock_sb.auth.get_user.return_value = mock_user_resp


def _mock_db_chain(mock_sb, data):
    """
    Mock a Supabase fluent chain:
    .from_().select().eq().single().execute() → data
    Used by check_usage_limit.
    """
    mock_result = MagicMock()
    mock_result.data = data
    (mock_sb
        .from_.return_value
        .select.return_value
        .eq.return_value
        .single.return_value
        .execute.return_value) = mock_result


# ──────────────────────────────────────────────────────────────
# SMOKE TEST 1 — Health endpoint
# ──────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    """
    GET /api/v1/health returns 200 with correct shape.
    Supabase ping is mocked to avoid real network call.
    """
    with patch("app.routes.health.supabase") as mock_sb:
        # Simulate a fast, successful DB ping
        mock_table = MagicMock()
        mock_sb.table.return_value = mock_table
        mock_table.select.return_value.limit.return_value.execute.return_value = MagicMock()

        resp = client.get("/api/v1/health")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert data["checks"]["database"]["status"] == "ok"


# ──────────────────────────────────────────────────────────────
# SMOKE TEST 2 — Signup → Login → Me full auth flow
# ──────────────────────────────────────────────────────────────

def test_full_auth_flow(client):
    """
    POST /signup → POST /login → GET /me
    Verifies the full auth chain works in sequence.
    """
    signup_payload = {
        "email": "smoke@example.com",
        "password": "securepass123",
        "business_name": "Smoke Cafe",
        "business_type": "restaurant",
    }
    login_payload = {
        "email": "smoke@example.com",
        "password": "securepass123",
    }

    # Step 1: Signup
    with patch("app.routes.auth.supabase") as mock_sb, \
         patch("app.routes.auth.create_user", return_value=FAKE_USER_ROW):
        mock_sb.auth.sign_up.return_value = _make_auth_response()
        signup_resp = client.post("/api/v1/auth/signup", json=signup_payload)

    assert signup_resp.status_code == 201

    # Step 2: Login
    with patch("app.routes.auth.supabase") as mock_sb, \
         patch("app.routes.auth.get_user_by_id", return_value=FAKE_USER_ROW):
        mock_sb.auth.sign_in_with_password.return_value = _make_auth_response()
        login_resp = client.post("/api/v1/auth/login", json=login_payload)

    assert login_resp.status_code == 200
    assert "session_token" in login_resp.headers.get("Set-Cookie", "")

    # Step 3: Me
    mock_user_resp = MagicMock()
    mock_user_resp.user = MagicMock(id=FAKE_USER_ID)

    with patch("app.utils.decorators.supabase") as mock_dec_sb, \
         patch("app.utils.decorators.get_user_by_id", return_value=FAKE_USER_ROW):
        mock_dec_sb.auth.get_user.return_value = mock_user_resp
        client.set_cookie("session_token", "smoke.fake.jwt")
        me_resp = client.get("/api/v1/auth/me")

    assert me_resp.status_code == 200
    data = me_resp.get_json()
    assert data["user"]["id"] == FAKE_USER_ID


# ──────────────────────────────────────────────────────────────
# SMOKE TEST 3 — Generate reply full path
# ──────────────────────────────────────────────────────────────

def test_generate_reply_full_path(client):
    """
    POST /api/v1/reviews/generate with valid payload.
    Verifies: schema → usage check → AI engine → reply saved → 201.
    """
    payload = {
        "rating": 4,
        "review_text": "Great service, will return.",
        "reviewer_name": "John",
    }

    usage_db_data = {
        "plan": "free",
        "reply_count_this_month": 0,
        "billing_cycle_start": "2026-03-01",
    }

    with patch("app.utils.decorators.supabase") as mock_dec_sb, \
         patch("app.utils.decorators.get_user_by_id", return_value=FAKE_USER_ROW), \
         patch("app.services.usage_service.supabase") as mock_usage_sb, \
         patch("app.models.review_model.supabase") as mock_review_sb, \
         patch("app.models.reply_model.supabase") as mock_reply_sb, \
         patch("app.models.review_model.update_review_status"), \
         patch("app.routes.reviews.generate_reply",
               return_value="Thank you for visiting!"), \
         patch("app.routes.reviews.increment_usage"):

        # Auth decorator
        mock_dec_sb.auth.get_user.return_value = MagicMock(
            user=MagicMock(id=FAKE_USER_ID)
        )

        # Usage check (live DB query)
        _mock_db_chain(mock_usage_sb, usage_db_data)

        # insert_review
        mock_review_result = MagicMock()
        mock_review_result.data = [FAKE_REVIEW_ROW]
        mock_review_sb.table.return_value.insert.return_value.execute.return_value = mock_review_result

        # insert_reply
        mock_reply_result = MagicMock()
        mock_reply_result.data = [FAKE_REPLY_ROW]
        mock_reply_sb.table.return_value.insert.return_value.execute.return_value = mock_reply_result

        client.set_cookie("session_token", "smoke.fake.jwt")
        resp = client.post("/api/v1/reviews/generate", json=payload)

    assert resp.status_code == 201
    data = resp.get_json()
    assert "reply" in data
    assert data["reply"]["id"] == FAKE_REPLY_ID
    assert data["reply"]["reply_text"] != ""


# ──────────────────────────────────────────────────────────────
# SMOKE TEST 4 — Review text over 2000 chars is rejected
# ──────────────────────────────────────────────────────────────

def test_generate_rejects_oversized_review(client):
    """
    POST /api/v1/reviews/generate with review_text > 2000 chars.
    Schema validation fires before any service call.
    """
    payload = {
        "rating": 4,
        "review_text": "x" * 2001,
        "reviewer_name": "John",
    }

    with patch("app.utils.decorators.supabase") as mock_dec_sb, \
         patch("app.utils.decorators.get_user_by_id", return_value=FAKE_USER_ROW):
        mock_dec_sb.auth.get_user.return_value = MagicMock(
            user=MagicMock(id=FAKE_USER_ID)
        )
        client.set_cookie("session_token", "smoke.fake.jwt")
        resp = client.post("/api/v1/reviews/generate", json=payload)

    assert resp.status_code == 400
    data = resp.get_json()
    assert data["code"] == "VALIDATION_ERROR"


# ──────────────────────────────────────────────────────────────
# SMOKE TEST 5 — Usage limit blocks at cap
# ──────────────────────────────────────────────────────────────

def test_generate_blocked_at_usage_limit(client):
    """
    POST /api/v1/reviews/generate when user is at their plan limit.
    Mock: usage_service DB query returns reply_count_this_month == 5, plan == "free".
    """
    payload = {
        "rating": 4,
        "review_text": "Great service!",
        "reviewer_name": "John",
    }

    at_limit_db_data = {
        "plan": "free",
        "reply_count_this_month": 5,
        "billing_cycle_start": "2026-03-01",
    }

    with patch("app.utils.decorators.supabase") as mock_dec_sb, \
         patch("app.utils.decorators.get_user_by_id", return_value=FAKE_USER_ROW), \
         patch("app.services.usage_service.supabase") as mock_usage_sb:

        mock_dec_sb.auth.get_user.return_value = MagicMock(
            user=MagicMock(id=FAKE_USER_ID)
        )
        _mock_db_chain(mock_usage_sb, at_limit_db_data)

        client.set_cookie("session_token", "smoke.fake.jwt")
        resp = client.post("/api/v1/reviews/generate", json=payload)

    assert resp.status_code == 403
    data = resp.get_json()
    assert data["code"] == "REPLY_LIMIT_REACHED"
    assert "replies_used" in data["details"]
    assert "replies_limit" in data["details"]


# ──────────────────────────────────────────────────────────────
# SMOKE TEST 6 — Stripe webhook valid signature
# ──────────────────────────────────────────────────────────────

def test_stripe_webhook_valid_event(client):
    """
    POST /api/v1/payments/webhook with a valid checkout.session.completed event.
    Mock: stripe.Webhook.construct_event returns a valid event.
    Mock: supabase plan update.
    """
    fake_event = MagicMock()
    fake_event.id = "evt_smoke_001"
    fake_event.type = "checkout.session.completed"
    fake_event.data.object = {
        "client_reference_id": FAKE_USER_ID,
        "customer": "cus_smoke_001",
    }

    with patch("app.services.stripe_service.stripe.Webhook.construct_event",
               return_value=fake_event), \
         patch("app.services.stripe_service.supabase") as mock_sb:

        # Mock the plan update chain
        mock_sb.from_.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        resp = client.post(
            "/api/v1/payments/webhook",
            data=b'{"type": "checkout.session.completed"}',
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=123,v1=abc",
            },
        )

    assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────
# SMOKE TEST 7 — Stripe webhook invalid signature rejected
# ──────────────────────────────────────────────────────────────

def test_stripe_webhook_invalid_signature(client):
    """
    POST /api/v1/payments/webhook with tampered body.
    Mock: stripe.Webhook.construct_event raises SignatureVerificationError.
    """
    import stripe as stripe_lib

    with patch("app.services.stripe_service.stripe.Webhook.construct_event",
               side_effect=stripe_lib.error.SignatureVerificationError(
                   "No signatures found matching the expected signature",
                   sig_header="bad-sig",
               )):
        resp = client.post(
            "/api/v1/payments/webhook",
            data=b'tampered-body',
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=bad,v1=bad",
            },
        )

    assert resp.status_code == 400
    data = resp.get_json()
    assert data["code"] == "STRIPE_WEBHOOK_INVALID"


# ──────────────────────────────────────────────────────────────
# SMOKE TEST 8 — Deleted user cookie rejected
# ──────────────────────────────────────────────────────────────

def test_deleted_user_cookie_rejected(client):
    """
    GET /api/v1/auth/me with a valid JWT but is_deleted=True on the user row.
    Verifies require_auth blocks the request with 401.
    """
    deleted_user = {**FAKE_USER_ROW, "is_deleted": True}

    mock_user_resp = MagicMock()
    mock_user_resp.user = MagicMock(id=FAKE_USER_ID)

    with patch("app.utils.decorators.supabase") as mock_dec_sb, \
         patch("app.utils.decorators.get_user_by_id", return_value=deleted_user):
        mock_dec_sb.auth.get_user.return_value = mock_user_resp

        client.set_cookie("session_token", "smoke.fake.jwt")
        resp = client.get("/api/v1/auth/me")

    assert resp.status_code == 401
    data = resp.get_json()
    assert data["code"] == "AUTH_REQUIRED"
