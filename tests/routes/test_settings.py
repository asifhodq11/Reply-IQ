"""
tests/routes/test_settings.py
Tests for Phase 5: Settings + History
"""

import os

# Env vars required before app factory runs
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
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
# Shared Mock Data
# ──────────────────────────────────────────────────────────────

FAKE_USER_ID = 'aaaaaaaa-0000-0000-0000-aaaaaaaaaaaa'

FAKE_USER_ROW = {
    'id': FAKE_USER_ID,
    'email': 'owner@example.com',
    'business_name': 'Old Name',
    'tone_preference': 'casual',
    'approval_tier': 1,
    'plan': 'free',
    'google_connected': False,
    'google_status': 'none',
    'reply_count_this_month': 0
}

# ──────────────────────────────────────────────────────────────
# Fake Supabase client for simulating DB ops in memory
# ──────────────────────────────────────────────────────────────

class MockQueryBuilder:
    def __init__(self, table, fake_db):
        self.table = table
        self.fake_db = fake_db
        self.filters = {}
        self._updates = None
        self._single = False
        self._count_type = None

    def select(self, *args, **kwargs):
        self._count_type = kwargs.get('count')
        return self

    def eq(self, column, value):
        self.filters[column] = value
        return self

    def single(self):
        self._single = True
        return self

    def update(self, updates):
        self._updates = updates
        return self
        
    def order(self, *args, **kwargs):
        return self
        
    def range(self, *args, **kwargs):
        return self

    def execute(self):
        # Update mode
        if self._updates is not None:
            for row in self.fake_db.get(self.table, []):
                match = True
                for col, val in self.filters.items():
                    if row.get(col) != val:
                        match = False
                        break
                if match:
                    row.update(self._updates)
            return MagicMock(data=None)
            
        # Select mode
        results = []
        for row in self.fake_db.get(self.table, []):
            match = True
            for col, val in self.filters.items():
                if row.get(col) != val:
                    match = False
                    break
            if match:
                results.append(dict(row))

        resp = MagicMock()
        if self._single:
            resp.data = results[0] if results else None
        else:
            resp.data = results
        if self._count_type:
            resp.count = len(results)
        return resp

class FakeSupabase:
    def __init__(self):
        self.db = {
            'users': [dict(FAKE_USER_ROW)],
            'reviews': []
        }
    def from_(self, table):
        return MockQueryBuilder(table, self.db)


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────

@pytest.fixture()
def app():
    application = create_app('testing')
    application.config['TESTING'] = True
    application.config['FORCE_HTTPS'] = False
    yield application

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def fake_db():
    fake_sb = FakeSupabase()
    # Ensure imported copies of supabase in routes are replaced
    with patch('app.routes.settings.supabase', fake_sb), \
         patch('app.routes.reviews.supabase', fake_sb):
        yield fake_sb.db

@pytest.fixture()
def auth_client(client):
    """Authenticated client matching the decorator checks."""
    mock_user = MagicMock()
    mock_user.id = FAKE_USER_ID
    mock_response = MagicMock()
    mock_response.user = mock_user

    with patch('app.utils.decorators.supabase') as mock_sb, \
         patch('app.utils.decorators.get_user_by_id', return_value=FAKE_USER_ROW):
         
        mock_sb.auth.get_user.return_value = mock_response
        client.set_cookie('session_token', 'fake.jwt.token')
        yield client


# ──────────────────────────────────────────────────────────────
# TEST 1 — PATCH /settings with valid fields returns 200
# ──────────────────────────────────────────────────────────────
def test_patch_settings_valid(auth_client, fake_db):
    resp = auth_client.patch('/api/v1/settings/', json={"business_name": "New Name"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['business_name'] == "New Name"
    # Ensure DB was updated
    assert fake_db['users'][0]['business_name'] == "New Name"


# ──────────────────────────────────────────────────────────────
# TEST 2 — PATCH /settings with unknown field returns 400
# ──────────────────────────────────────────────────────────────
def test_patch_settings_unknown_field(auth_client, fake_db):
    resp = auth_client.patch('/api/v1/settings/', json={"plan": "pro"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] is True
    assert data['code'] == 'VALIDATION_ERROR'


# ──────────────────────────────────────────────────────────────
# TEST 3 — PATCH /settings with invalid tone returns 400
# ──────────────────────────────────────────────────────────────
def test_patch_settings_invalid_tone(auth_client, fake_db):
    resp = auth_client.patch('/api/v1/settings/', json={"tone_preference": "aggressive"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] is True
    assert data['code'] == 'VALIDATION_ERROR'


# ──────────────────────────────────────────────────────────────
# TEST 4 — PATCH /settings with invalid approval_tier returns 400
# ──────────────────────────────────────────────────────────────
def test_patch_settings_invalid_tier(auth_client, fake_db):
    resp = auth_client.patch('/api/v1/settings/', json={"approval_tier": 5})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] is True
    assert data['code'] == 'VALIDATION_ERROR'


# ──────────────────────────────────────────────────────────────
# TEST 5 — GET /settings returns 200 with correct fields
# ──────────────────────────────────────────────────────────────
def test_get_settings_correct_fields(auth_client, fake_db):
    resp = auth_client.get('/api/v1/settings/')
    assert resp.status_code == 200
    data = resp.get_json()
    
    expected_fields = [
        'business_name', 'tone_preference', 'approval_tier', 'plan',
        'google_connected', 'google_status', 'reply_count_this_month'
    ]
    for key in expected_fields:
        assert key in data


# ──────────────────────────────────────────────────────────────
# TEST 6 — GET /reviews/history returns paginated results
# ──────────────────────────────────────────────────────────────
def test_history_paginated(auth_client, fake_db):
    fake_db['reviews'].append({
        'id': 'r1', 'user_id': FAKE_USER_ID, 'is_deleted': False,
        'review_text': 'test item', 'star_rating': 5, 'reviewer_name': 'Joe',
        'platform': 'google', 'status': 'pending', 'created_at': '2026-03-22T00:00:00Z'
    })
    
    resp = auth_client.get('/api/v1/reviews/history')
    assert resp.status_code == 200
    data = resp.get_json()
    
    assert 'items' in data
    assert 'total' in data
    assert 'has_more' in data
    assert data['total'] == 1
    assert len(data['items']) == 1


# ──────────────────────────────────────────────────────────────
# TEST 7 — GET /reviews/history never returns soft-deleted reviews
# ──────────────────────────────────────────────────────────────
def test_history_hides_deleted(auth_client, fake_db):
    # One visible review
    fake_db['reviews'].append({
        'id': 'r1', 'user_id': FAKE_USER_ID, 'is_deleted': False,
        'review_text': 'keep me', 'star_rating': 5, 'reviewer_name': 'A',
        'platform': 'google', 'status': 'pending', 'created_at': '2026-03-22T00:00:00Z'
    })
    # One soft-deleted review
    fake_db['reviews'].append({
        'id': 'r2', 'user_id': FAKE_USER_ID, 'is_deleted': True,
        'review_text': 'hide me', 'star_rating': 1, 'reviewer_name': 'B',
        'platform': 'google', 'status': 'pending', 'created_at': '2026-03-22T00:00:00Z'
    })

    resp = auth_client.get('/api/v1/reviews/history')
    assert resp.status_code == 200
    data = resp.get_json()
    
    assert data['total'] == 1
    assert len(data['items']) == 1
    assert data['items'][0]['id'] == 'r1'


# ──────────────────────────────────────────────────────────────
# TEST 8 — GET /reviews/history without auth returns 401
# ──────────────────────────────────────────────────────────────
def test_history_no_auth(client):
    resp = client.get('/api/v1/reviews/history')
    assert resp.status_code == 401
    assert resp.get_json()['code'] == 'AUTH_REQUIRED'


# ──────────────────────────────────────────────────────────────
# TEST 9 — GET /settings without auth returns 401
# ──────────────────────────────────────────────────────────────
def test_settings_no_auth(client):
    resp = client.get('/api/v1/settings/')
    assert resp.status_code == 401
    assert resp.get_json()['code'] == 'AUTH_REQUIRED'
