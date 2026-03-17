-- ============================================================
-- Migration 002: reviews
-- ============================================================

-- STEP 1: CREATE TABLE
CREATE TABLE IF NOT EXISTS reviews (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    google_review_id TEXT,
    reviewer_name    TEXT,
    rating           INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text      TEXT,
    review_date      TIMESTAMPTZ,
    location_id      TEXT,
    status           TEXT NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending', 'processing', 'replied', 'failed', 'skipped')),
    is_deleted       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 2: ENABLE RLS
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;

-- STEP 3: POLICY — SELECT
-- Users can only see their own non-deleted reviews
CREATE POLICY "reviews_select"
ON reviews
FOR SELECT
USING (
    auth.uid() = user_id
    AND is_deleted = FALSE
);

-- STEP 4: POLICY — INSERT / UPDATE / DELETE
CREATE POLICY "reviews_insert"
ON reviews
FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "reviews_update"
ON reviews
FOR UPDATE
USING (auth.uid() = user_id AND is_deleted = FALSE)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "reviews_delete"
ON reviews
FOR DELETE
USING (auth.uid() = user_id);

-- STEP 5: CREATE INDEX
CREATE INDEX IF NOT EXISTS idx_reviews_user_id
    ON reviews (user_id);

CREATE INDEX IF NOT EXISTS idx_reviews_status
    ON reviews (status);

-- Partial index — only index rows that have a real Google review ID
CREATE UNIQUE INDEX IF NOT EXISTS idx_reviews_google_review_id
    ON reviews (google_review_id)
    WHERE google_review_id IS NOT NULL;
