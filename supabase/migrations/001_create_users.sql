-- ============================================================
-- Migration 001: users
-- ============================================================

-- STEP 1: CREATE TABLE
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT NOT NULL UNIQUE,
    business_name   TEXT,
    gbp_location_id TEXT,
    google_token    JSONB,
    tier            TEXT NOT NULL DEFAULT 'smart_review'
                        CHECK (tier IN ('auto_post', 'smart_review', 'manual_approve')),
    plan            TEXT NOT NULL DEFAULT 'starter'
                        CHECK (plan IN ('starter', 'growth', 'enterprise')),
    replies_used    INTEGER NOT NULL DEFAULT 0,
    replies_limit   INTEGER NOT NULL DEFAULT 50,
    stripe_customer_id     TEXT,
    stripe_subscription_id TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 2: ENABLE RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- STEP 3: POLICY — SELECT
-- Users can only read their own non-deleted row
CREATE POLICY "users_select"
ON users
FOR SELECT
USING (
    auth.uid() = id
    AND is_deleted = FALSE
);

-- STEP 4: POLICY — INSERT / UPDATE / DELETE
CREATE POLICY "users_insert"
ON users
FOR INSERT
WITH CHECK (auth.uid() = id);

CREATE POLICY "users_update"
ON users
FOR UPDATE
USING (auth.uid() = id AND is_deleted = FALSE)
WITH CHECK (auth.uid() = id);

CREATE POLICY "users_delete"
ON users
FOR DELETE
USING (auth.uid() = id);

-- STEP 5: CREATE INDEX
CREATE INDEX IF NOT EXISTS idx_users_email
    ON users (email);

CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id
    ON users (stripe_customer_id);

CREATE INDEX IF NOT EXISTS idx_users_gbp_location_id
    ON users (gbp_location_id);
