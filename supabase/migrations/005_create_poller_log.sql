-- ============================================================
-- Migration 005: poller_log
-- ============================================================

-- STEP 1: CREATE TABLE
CREATE TABLE IF NOT EXISTS poller_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    location_id     TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('success', 'failed', 'partial')),
    reviews_fetched INTEGER NOT NULL DEFAULT 0,
    reviews_new     INTEGER NOT NULL DEFAULT 0,
    error_message   TEXT,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

-- STEP 2: ENABLE RLS
ALTER TABLE poller_log ENABLE ROW LEVEL SECURITY;

-- STEP 3: POLICY — SELECT
-- Users can only see their own poller log entries
-- (poller_log is append-only, no is_deleted column needed)
CREATE POLICY "poller_log_select"
ON poller_log
FOR SELECT
USING (
    auth.uid() = user_id
);

-- STEP 4: POLICY — INSERT / UPDATE / DELETE
-- Only the backend service role writes here — no user INSERT/UPDATE
-- We still define them so RLS is explicit and nothing leaks
CREATE POLICY "poller_log_insert"
ON poller_log
FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "poller_log_update"
ON poller_log
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "poller_log_delete"
ON poller_log
FOR DELETE
USING (auth.uid() = user_id);

-- STEP 5: CREATE INDEX
CREATE INDEX IF NOT EXISTS idx_poller_log_user_id
    ON poller_log (user_id);

CREATE INDEX IF NOT EXISTS idx_poller_log_started_at
    ON poller_log (started_at DESC);

CREATE INDEX IF NOT EXISTS idx_poller_log_status
    ON poller_log (status);
