"""
tests/routes/test_auth.py

8 auth tests — all Supabase calls are mocked.
No real network calls. No .env.test required.

Test IDs (as specified in Phase 3 requirements):
1. POST /signup  valid data         → 201 + cookie set
2. POST /signup  duplicate email    → 409 EMAIL_EXISTS
3. POST /signup  missing fields     → 400 VALIDATION_ERROR
4. POST /signup  password < 8 chars → 400 VALIDATION_ERROR
5. POST /login   correct creds      → 200 + cookie set
6. POST /login   wrong password     → 401 INVALID_CREDENTIALS
7. GET  /me      valid cookie       → 200 + user object
8. GET  /me      no cookie          → 401 AUTH_REQUIRED
"""

import os

# Set dummy env vars BEFORE any app imports
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'

# Supabase enforces JWT format validation at client creation
FAKE_JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSJ9.fake_signature_for_testing'
os.environ['SUPABASE_ANON_KEY'] = FAKE_JWT
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = FAKE_JWT

os.environ['OPENAI_API_KEY'] = 'test-openai-key'
os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
os.environ['GOOGLE_API_KEY'] = 'test-google-key'
os.environ['STRIPE_SECRET_KEY'] = 'test-stripe-key'
os.environ['STRIPE_WEBHOOK_SECRET'] = 'test-webhook-secret'
os.environ['STRIPE_PRICE_ID_STARTER'] = 'test-price-id'
os.environ['RESEND_API_KEY'] = 'test-resend-key'
os.environ['FRONTEND_URL'] = 'http://test.localhost'

import pytest
from unittest.mock import MagicMock, patch

from app import create_app


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────

@pytest.fixture()
def app():
    """Flask app in testing mode with Talisman disabled."""
    application = create_app('testing')
    application.config['TESTING'] = True
    # Talisman blocks plain HTTP in tests — disable HTTPS enforcement
    application.config['FORCE_HTTPS'] = False
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


# ── Shared mock data ──────────────────────────────────────────

FAKE_USER_ID = 'aaaaaaaa-0000-0000-0000-aaaaaaaaaaaa'

FAKE_USER_ROW = {
    'id':                        FAKE_USER_ID,
    'email':                     'owner@example.com',
    'business_name':             'Test Cafe',
    'business_type':             'restaurant',
    'tone_preference':           'friendly',
    'plan':                      'free',
    'reply_count_this_month':    0,
    'billing_cycle_start':       '2026-03-18',
    'approval_tier':             2,
    'google_connected':          False,
    'google_status':             'none',
    'google_location_id':        None,
    'stripe_customer_id':        None,
    'consecutive_poll_failures': 0,
    'cancellation_reason':       None,
    'time_to_first_value_ms':    None,
    'is_deleted':                False,
    'created_at':                '2026-03-18T00:00:00Z',
}

VALID_SIGNUP_PAYLOAD = {
    'email':         'owner@example.com',
    'password':      'securepass123',
    'business_name': 'Test Cafe',
    'business_type': 'restaurant',
}

VALID_LOGIN_PAYLOAD = {
    'email':    'owner@example.com',
    'password': 'securepass123',
}


def _make_auth_response(user_id=FAKE_USER_ID):
    """Build a fake Supabase auth response with a session."""
    mock_user    = MagicMock()
    mock_user.id = user_id

    mock_session              = MagicMock()
    mock_session.access_token = 'fake.jwt.token'

    mock_response         = MagicMock()
    mock_response.user    = mock_user
    mock_response.session = mock_session
    return mock_response


# ──────────────────────────────────────────────────────────────
# Test 1 — POST /signup valid data → 201 + session cookie set
# ──────────────────────────────────────────────────────────────

def test_signup_valid(client):
    with patch('app.routes.auth.supabase') as mock_sb, \
         patch('app.routes.auth.create_user', return_value=FAKE_USER_ROW):

        mock_sb.auth.sign_up.return_value = _make_auth_response()

        resp = client.post('/api/v1/auth/signup', json=VALID_SIGNUP_PAYLOAD)

    assert resp.status_code == 201
    data = resp.get_json()
    assert data['user']['id'] == FAKE_USER_ID
    # Cookie must be set
    assert 'session_token' in resp.headers.get('Set-Cookie', '')


# ──────────────────────────────────────────────────────────────
# Test 2 — POST /signup duplicate email → 409 EMAIL_EXISTS
# ──────────────────────────────────────────────────────────────

def test_signup_duplicate_email(client):
    with patch('app.routes.auth.supabase') as mock_sb:
        mock_sb.auth.sign_up.side_effect = Exception('User already registered')

        resp = client.post('/api/v1/auth/signup', json=VALID_SIGNUP_PAYLOAD)

    assert resp.status_code == 409
    data = resp.get_json()
    assert data['error'] is True
    assert data['code'] == 'EMAIL_EXISTS'


# ──────────────────────────────────────────────────────────────
# Test 3 — POST /signup missing required fields → 400 VALIDATION_ERROR
# ──────────────────────────────────────────────────────────────

def test_signup_missing_fields(client):
    # Omit business_name and business_type
    resp = client.post('/api/v1/auth/signup', json={
        'email':    'owner@example.com',
        'password': 'securepass123',
    })

    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] is True
    assert data['code'] == 'VALIDATION_ERROR'
    assert 'business_name' in data['details']
    assert 'business_type' in data['details']


# ──────────────────────────────────────────────────────────────
# Test 4 — POST /signup password under 8 chars → 400 VALIDATION_ERROR
# ──────────────────────────────────────────────────────────────

def test_signup_short_password(client):
    resp = client.post('/api/v1/auth/signup', json={
        **VALID_SIGNUP_PAYLOAD,
        'password': 'short',
    })

    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] is True
    assert data['code'] == 'VALIDATION_ERROR'
    assert 'password' in data['details']


# ──────────────────────────────────────────────────────────────
# Test 5 — POST /login correct credentials → 200 + cookie set
# ──────────────────────────────────────────────────────────────

def test_login_valid(client):
    with patch('app.routes.auth.supabase') as mock_sb, \
         patch('app.routes.auth.get_user_by_id', return_value=FAKE_USER_ROW):

        mock_sb.auth.sign_in_with_password.return_value = _make_auth_response()

        resp = client.post('/api/v1/auth/login', json=VALID_LOGIN_PAYLOAD)

    assert resp.status_code == 200
    data = resp.get_json()
    assert data['user']['id'] == FAKE_USER_ID
    assert 'session_token' in resp.headers.get('Set-Cookie', '')


# ──────────────────────────────────────────────────────────────
# Test 6 — POST /login wrong password → 401 INVALID_CREDENTIALS
# ──────────────────────────────────────────────────────────────

def test_login_wrong_password(client):
    with patch('app.routes.auth.supabase') as mock_sb:
        mock_sb.auth.sign_in_with_password.side_effect = Exception('Invalid login credentials')

        resp = client.post('/api/v1/auth/login', json=VALID_LOGIN_PAYLOAD)

    assert resp.status_code == 401
    data = resp.get_json()
    assert data['error'] is True
    assert data['code'] == 'INVALID_CREDENTIALS'


# ──────────────────────────────────────────────────────────────
# Test 7 — GET /me with valid session cookie → 200 + user object
# ──────────────────────────────────────────────────────────────

def test_me_with_valid_cookie(client):
    mock_user_response      = MagicMock()
    mock_user_response.user = MagicMock(id=FAKE_USER_ID)

    with patch('app.utils.decorators.supabase') as mock_sb, \
         patch('app.utils.decorators.get_user_by_id', return_value=FAKE_USER_ROW):

        mock_sb.auth.get_user.return_value = mock_user_response

        client.set_cookie('session_token', 'fake.jwt.token')
        resp = client.get('/api/v1/auth/me')

    assert resp.status_code == 200
    data = resp.get_json()
    assert data['user']['id'] == FAKE_USER_ID
    assert data['user']['email'] == 'owner@example.com'


# ──────────────────────────────────────────────────────────────
# Test 8 — GET /me with no cookie → 401 AUTH_REQUIRED
# ──────────────────────────────────────────────────────────────

def test_me_no_cookie(client):
    # No cookie header — no patches needed
    resp = client.get('/api/v1/auth/me')

    assert resp.status_code == 401
    data = resp.get_json()
    assert data['error'] is True
    assert data['code'] == 'AUTH_REQUIRED'
