"""
tests/security/test_tenant_isolation.py

Security tests to ensure strict tenant isolation (OWASP API1 / BOLA).
Verifies that User A cannot access, modify, or delete User B's data.
"""

import os
import pytest
from unittest.mock import MagicMock, patch, call

# Set dummy env vars BEFORE any app imports
os.environ["SECRET_KEY"] = "test-secret"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
FAKE_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSJ9.fake"
os.environ["SUPABASE_ANON_KEY"] = FAKE_JWT
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = FAKE_JWT
os.environ["OPENAI_API_KEY"] = "test"
os.environ["GEMINI_API_KEY"] = "test"
os.environ["GOOGLE_API_KEY"] = "test"
os.environ["STRIPE_SECRET_KEY"] = "test"
os.environ["STRIPE_WEBHOOK_SECRET"] = "test"
os.environ["STRIPE_PRICE_ID_STARTER"] = "price_starter"
os.environ["RESEND_API_KEY"] = "test"
os.environ["FRONTEND_URL"] = "http://test.localhost"

from app import create_app

# ──────────────────────────────────────────────────────────────
# Mock Users
# ──────────────────────────────────────────────────────────────

USER_A = {
    "id": "user-a-1111",
    "email": "a@test.com",
    "plan": "starter",
    "business_name": "A Biz",
    "business_type": "cafe",
    "tone_preference": "friendly",
    "approval_tier": 2,
    "reply_count_this_month": 0,
    "billing_cycle_start": "2026-03-24",
    "google_connected": False,
    "google_status": "none",
    "is_deleted": False,
}

USER_B = {
    "id": "user-b-2222",
    "email": "b@test.com",
    "plan": "starter",
    "business_name": "B Biz",
    "business_type": "shop",
    "tone_preference": "formal",
    "approval_tier": 1,
    "reply_count_this_month": 0,
    "billing_cycle_start": "2026-03-24",
    "google_connected": False,
    "google_status": "none",
    "is_deleted": False,
}


# ──────────────────────────────────────────────────────────────
# In-Memory Supabase Mock
# ──────────────────────────────────────────────────────────────

class MockQueryBuilder:
    def __init__(self, table, db):
        self.table = table
        self.db = db
        self.filters = {}
        self._updates = None
        self._inserted = None
        self._single = False

    def select(self, *a, **kw):
        return self

    def eq(self, c, v):
        self.filters[c] = v
        return self

    def single(self):
        self._single = True
        return self

    def order(self, *a, **kw):
        return self

    def range(self, *a, **kw):
        return self

    def update(self, u):
        self._updates = u
        return self

    def insert(self, d):
        items = [dict(i) for i in d] if isinstance(d, list) else [dict(d)]
        if self.table not in self.db:
            self.db[self.table] = []
        for item in items:
            item.setdefault("id", f"new-{len(self.db[self.table])}")
            self.db[self.table].append(item)
        self._inserted = items
        return self

    def execute(self):
        # INSERT
        if self._inserted is not None:
            return MagicMock(data=self._inserted)

        # Filter rows
        rows = self.db.get(self.table, [])
        matched = [r for r in rows if all(r.get(c) == v for c, v in self.filters.items())]

        # UPDATE
        if self._updates is not None:
            for r in matched:
                r.update(self._updates)
            return MagicMock(data=matched)

        # SELECT
        resp = MagicMock()
        resp.data = matched[0] if (self._single and matched) else matched
        resp.count = len(matched)
        return resp


class FakeSupabase:
    def __init__(self):
        self.db = {
            "users": [],
            "reviews": [],
            "replies": [],
            "approval_tokens": [],
        }
        self.auth = MagicMock()

    def from_(self, t):
        return MockQueryBuilder(t, self.db)

    # review_model.py / reply_model.py use .table() not .from_()
    def table(self, t):
        return self.from_(t)

    def rpc(self, *a, **kw):
        return MagicMock(execute=lambda: MagicMock(data=None))


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────


@pytest.fixture()
def app():
    application = create_app("testing")
    application.config["TESTING"] = True
    application.config["FORCE_HTTPS"] = False
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def fake_sb():
    fsb = FakeSupabase()
    fsb.db["users"] = [dict(USER_A), dict(USER_B)]
    fsb.db["reviews"] = [
        {"id": "r-a", "user_id": USER_A["id"], "review_text": "A", "star_rating": 5, "is_deleted": False},
        {"id": "r-b", "user_id": USER_B["id"], "review_text": "B", "star_rating": 5, "is_deleted": False},
    ]

    def _get_user(uid):
        return next((u for u in fsb.db["users"] if u["id"] == uid), None)

    patches = [
        patch("app.extensions.supabase", fsb),
        patch("app.utils.decorators.supabase", fsb),
        patch("app.utils.decorators.get_user_by_id", side_effect=_get_user),
        patch("app.routes.auth.supabase", fsb),
        patch("app.routes.reviews.supabase", fsb),
        patch("app.routes.settings.supabase", fsb),
        patch("app.routes.approvals.supabase", fsb),
        patch("app.models.user_model.supabase", fsb),
        patch("app.models.review_model.supabase", fsb),
        patch("app.models.reply_model.supabase", fsb),
        patch("app.models.token_model.supabase", fsb),
        # Bypass usage counting to focus on isolation behaviour
        patch("app.routes.reviews.check_usage_limit", return_value={"allowed": True}),
        patch("app.routes.reviews.increment_usage", return_value=None),
    ]
    for p in patches:
        p.start()
    yield fsb
    for p in patches:
        p.stop()


@pytest.fixture()
def auth_a(client, fake_sb):
    """Authenticated client acting as User A."""
    mock_resp = MagicMock()
    mock_resp.user.id = USER_A["id"]
    fake_sb.auth.get_user.return_value = mock_resp
    client.set_cookie("session_token", "jwt-a")
    return client


# ──────────────────────────────────────────────────────────────
# TEST 1 — History is scoped to authenticated tenant
# ──────────────────────────────────────────────────────────────

def test_user_a_cannot_see_user_b_reviews(auth_a, fake_sb):
    """GET /history must only return User A's reviews, never User B's."""
    resp = auth_a.get("/api/v1/reviews/history")
    assert resp.status_code == 200
    data = resp.get_json()
    ids = [item["id"] for item in data["items"]]
    assert "r-a" in ids
    assert "r-b" not in ids


# ──────────────────────────────────────────────────────────────
# TEST 2 — Settings PATCH is scoped to authenticated tenant
# ──────────────────────────────────────────────────────────────

def test_user_a_cannot_patch_user_b_settings(auth_a, fake_sb):
    """PATCH /settings must only update User A's row in the DB."""
    resp = auth_a.patch("/api/v1/settings/", json={"business_name": "A Modified"})
    assert resp.status_code == 200

    user_a = next(u for u in fake_sb.db["users"] if u["id"] == USER_A["id"])
    user_b = next(u for u in fake_sb.db["users"] if u["id"] == USER_B["id"])

    assert user_a["business_name"] == "A Modified"
    assert user_b["business_name"] == "B Biz"  # Isolation confirmed


# ──────────────────────────────────────────────────────────────
# TEST 3 — AI generation inserts records with authenticated user_id
# ──────────────────────────────────────────────────────────────

def test_user_a_cannot_generate_reply_as_user_b(auth_a, fake_sb):
    """POST /generate must tag all created DB records with User A's user_id."""
    payload = {"rating": 5, "review_text": "Great visit!", "reviewer_name": "Tester", "google_review_id": "G-1"}

    with patch("app.routes.reviews.generate_reply", return_value="AI reply text"):
        resp = auth_a.post("/api/v1/reviews/generate", json=payload)

    assert resp.status_code == 201
    data = resp.get_json()

    # Verify the DB rows that were inserted belong to User A
    review = data["review"]
    reply = data["reply"]
    assert review["user_id"] == USER_A["id"]
    assert reply["user_id"] == USER_A["id"]
    assert review["user_id"] != USER_B["id"]
    assert reply["user_id"] != USER_B["id"]


# ──────────────────────────────────────────────────────────────
# TEST 4 — Approval token update is scoped to its owner's user_id
# ──────────────────────────────────────────────────────────────

def test_approval_token_scoped_to_owner(client, fake_sb):
    """POST /approve/<token> must never update data belonging to another user."""
    # User B owns a reply
    fake_sb.db["replies"].append({"id": "rep-b", "user_id": USER_B["id"], "reply_text": "Original B"})
    # Token owned by User A, but constructed to point at User B's reply
    fake_sb.db["approval_tokens"].append({
        "token": "tok-a", "user_id": USER_A["id"], "used": False,
        "expires_at": "2099-01-01T00:00:00Z", "reply_id": "rep-b"
    })

    # Patch model helpers — the route uses them directly
    token_row = fake_sb.db["approval_tokens"][0]
    reply_row = fake_sb.db["replies"][0]

    with patch("app.routes.approvals.get_token", return_value=token_row), \
         patch("app.routes.approvals.get_reply_for_token", return_value=reply_row), \
         patch("app.routes.approvals.consume_token", return_value=True), \
         patch("app.routes.approvals.post_reply_to_google"):
        # Send different text — attempting to overwrite User B's reply
        resp = client.post("/api/v1/approve/tok-a", json={"reply_text": "Hijacked!"})

    assert resp.status_code == 200

    # The .update() in approvals.py filters by BOTH reply id AND user_id
    # Since user_id in the reply belongs to USER_B but token's user_id is USER_A,
    # the DB update matches 0 rows, leaving the reply untouched.
    rep_b = next(r for r in fake_sb.db["replies"] if r["id"] == "rep-b")
    assert rep_b["reply_text"] == "Original B"


# ──────────────────────────────────────────────────────────────
# TEST 5 — Account deletion only anonymises the requesting user
# ──────────────────────────────────────────────────────────────

def test_delete_account_only_affects_own_data(auth_a, fake_sb):
    """DELETE /auth/account must call anonymise_user with ONLY User A's ID."""
    # Patch the name bound in auth.py's namespace (imported at module top)
    with patch("app.routes.auth.anonymise_user") as mock_anon:
        resp = auth_a.delete("/api/v1/auth/account")

    assert resp.status_code == 200
    # Called exactly once with User A's ID
    mock_anon.assert_called_once_with(USER_A["id"])
    # User B's ID must never appear
    called_ids = [c.args[0] for c in mock_anon.call_args_list]
    assert USER_B["id"] not in called_ids
