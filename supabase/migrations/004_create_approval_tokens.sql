-- ============================================================
-- Migration 004: approval_tokens
-- ============================================================

-- STEP 1: CREATE TABLE
CREATE TABLE IF NOT EXISTS approval_tokens (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reply_id   UUID NOT NULL REFERENCES replies(id) ON DELETE CASCADE,
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token      TEXT NOT NULL UNIQUE DEFAULT gen_random_uuid()::TEXT,
    action     TEXT NOT NULL CHECK (action IN ('approve', 'reject')),
    used       BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '72 hours'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 2: ENABLE RLS
ALTER TABLE approval_tokens ENABLE ROW LEVEL SECURITY;

-- STEP 3: POLICY — SELECT
-- Users can only see their own non-expired, non-used tokens
CREATE POLICY "approval_tokens_select"
ON approval_tokens
FOR SELECT
USING (
    auth.uid() = user_id
    AND used = FALSE
    AND is_deleted = FALSE
);

-- STEP 4: POLICY — INSERT / UPDATE / DELETE
CREATE POLICY "approval_tokens_insert"
ON approval_tokens
FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "approval_tokens_update"
ON approval_tokens
FOR UPDATE
USING (auth.uid() = user_id AND used = FALSE)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "approval_tokens_delete"
ON approval_tokens
FOR DELETE
USING (auth.uid() = user_id);

-- STEP 5: CREATE INDEX
CREATE INDEX IF NOT EXISTS idx_approval_tokens_user_id
    ON approval_tokens (user_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_approval_tokens_token
    ON approval_tokens (token);

CREATE INDEX IF NOT EXISTS idx_approval_tokens_reply_id
    ON approval_tokens (reply_id);
