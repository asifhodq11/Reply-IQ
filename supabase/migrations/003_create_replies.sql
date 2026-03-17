-- ============================================================
-- Migration 003: replies
-- ============================================================

-- STEP 1: CREATE TABLE
CREATE TABLE IF NOT EXISTS replies (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id   UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reply_text  TEXT NOT NULL,
    ai_model    TEXT,
    status      TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'posted', 'rejected', 'failed')),
    approved_at TIMESTAMPTZ,
    posted_at   TIMESTAMPTZ,
    is_deleted  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 2: ENABLE RLS
ALTER TABLE replies ENABLE ROW LEVEL SECURITY;

-- STEP 3: POLICY — SELECT
-- Users can only see their own non-deleted replies
CREATE POLICY "replies_select"
ON replies
FOR SELECT
USING (
    auth.uid() = user_id
    AND is_deleted = FALSE
);

-- STEP 4: POLICY — INSERT / UPDATE / DELETE
CREATE POLICY "replies_insert"
ON replies
FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "replies_update"
ON replies
FOR UPDATE
USING (auth.uid() = user_id AND is_deleted = FALSE)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "replies_delete"
ON replies
FOR DELETE
USING (auth.uid() = user_id);

-- STEP 5: CREATE INDEX
CREATE INDEX IF NOT EXISTS idx_replies_user_id
    ON replies (user_id);

CREATE INDEX IF NOT EXISTS idx_replies_review_id
    ON replies (review_id);

CREATE INDEX IF NOT EXISTS idx_replies_status
    ON replies (status);
