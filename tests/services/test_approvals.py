"""
tests/services/test_approvals.py

5 tests for Phase 7: Approvals & Tokens
Tests token-based 1-click approvals, expiration checking, 
already-used prevention, and double-click race conditions.
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# Set dummy env vars BEFORE any app imports
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
FAKE_JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSJ9.fake'
os.environ['SUPABASE_ANON_KEY'] = FAKE_JWT
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = FAKE_JWT
os.environ['OPENAI_API_KEY'] = 'test-openai-key'
os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
os.environ['GOOGLE_API_KEY'] = 'test-google-key'
os.environ['STRIPE_SECRET_KEY'] = 'test-stripe-key'
os.environ['STRIPE_WEBHOOK_SECRET'] = 'test-webhook-secret'
os.environ['STRIPE_PRICE_ID_STARTER'] = 'price_starter'
os.environ['RESEND_API_KEY'] = 'test-resend-key'
os.environ['FRONTEND_URL'] = 'http://test.localhost'

import pytest
from app import create_app
from app.utils.exceptions import TokenAlreadyUsed

@pytest.fixture()
def app():
    application = create_app('testing')
    application.config['TESTING'] = True
    yield application

@pytest.fixture()
def client(app):
    return app.test_client()


FAKE_REPLY = {'id': 'reply-1', 'reply_text': 'Hello'}


def _make_token(used=False, expired=False):
    """
    Returns a mocked token dictionary as Supabase would provide it,
    handling the explicit UTC timezone ISO formatting matching DB expectations.
    """
    expires = datetime.now(timezone.utc)
    if expired:
        expires -= timedelta(hours=1)
    else:
        expires += timedelta(hours=24)
        
    return {
        'token': 'fake-token-123',
        'used': used,
        'expires_at': expires.isoformat().replace('+00:00', 'Z'),
        'user_id': 'user-123'
    }


# ──────────────────────────────────────────────────────────────
# TEST 1 — Valid token GET returns 200 with reply text
# ──────────────────────────────────────────────────────────────
@patch('app.routes.approvals.get_token')
@patch('app.routes.approvals.get_reply_for_token')
def test_get_valid_token(mock_get_reply, mock_get_token, client):
    mock_get_token.return_value = _make_token()
    mock_get_reply.return_value = FAKE_REPLY
    
    resp = client.get('/api/v1/approve/fake-token')
    
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['token'] == 'fake-token'
    assert data['reply'] == FAKE_REPLY


# ──────────────────────────────────────────────────────────────
# TEST 2 — Expired token returns 410
# ──────────────────────────────────────────────────────────────
@patch('app.routes.approvals.get_token')
def test_get_expired_token(mock_get_token, client):
    mock_get_token.return_value = _make_token(expired=True)
    
    resp = client.get('/api/v1/approve/fake-token')
    
    assert resp.status_code == 410
    data = resp.get_json()
    assert data['error'] is True
    assert data['code'] == 'TOKEN_EXPIRED'


# ──────────────────────────────────────────────────────────────
# TEST 3 — Already used token returns 409
# ──────────────────────────────────────────────────────────────
@patch('app.routes.approvals.get_token')
def test_get_used_token(mock_get_token, client):
    mock_get_token.return_value = _make_token(used=True)
    
    resp = client.get('/api/v1/approve/fake-token')
    
    assert resp.status_code == 409
    data = resp.get_json()
    assert data['error'] is True
    assert data['code'] == 'TOKEN_USED'


# ──────────────────────────────────────────────────────────────
# TEST 4 — Invalid token returns 404
# ──────────────────────────────────────────────────────────────
@patch('app.routes.approvals.get_token')
def test_get_invalid_token(mock_get_token, client):
    mock_get_token.return_value = None
    
    resp = client.get('/api/v1/approve/fake-token')
    
    assert resp.status_code == 404
    data = resp.get_json()
    assert data['error'] is True
    assert data['code'] == 'TOKEN_INVALID'


# ──────────────────────────────────────────────────────────────
# TEST 5 — Double-click POST returns 409 on second call
# ──────────────────────────────────────────────────────────────
@patch('app.routes.approvals.post_reply_to_google')
@patch('app.routes.approvals.get_reply_for_token')
@patch('app.routes.approvals.consume_token')
@patch('app.routes.approvals.get_token')
def test_post_double_click_atomic(mock_get_token, mock_consume, mock_get_reply, mock_post, client):
    mock_get_token.return_value = _make_token()
    mock_get_reply.return_value = FAKE_REPLY
    
    # First click succeeds
    mock_consume.return_value = True
    resp1 = client.post('/api/v1/approve/fake-token')
    assert resp1.status_code == 200
    assert mock_post.called
    
    # Second click hits the DB race condition boundary — consume_token atomically raises
    mock_consume.side_effect = TokenAlreadyUsed()
    resp2 = client.post('/api/v1/approve/fake-token')
    assert resp2.status_code == 409
    assert resp2.get_json()['code'] == 'TOKEN_USED'
