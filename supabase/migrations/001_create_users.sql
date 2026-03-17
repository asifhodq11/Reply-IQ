-- ============================================================
-- Migration 001: users
-- ============================================================

-- STEP 1: CREATE TABLE
CREATE TABLE public.users (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                     TEXT UNIQUE NOT NULL,
    business_name             TEXT NOT NULL,
    business_type             TEXT NOT NULL,
    tone_preference           TEXT NOT NULL DEFAULT 'friendly',
    plan                      TEXT NOT NULL DEFAULT 'free',
    reply_count_this_month    INT NOT NULL DEFAULT 0,
    billing_cycle_start       DATE NOT NULL DEFAULT CURRENT_DATE,
    approval_tier             INT NOT NULL DEFAULT 2,
    google_connected          BOOL NOT NULL DEFAULT false,
    google_status             TEXT NOT NULL DEFAULT 'none',
    google_location_id        TEXT,
    stripe_customer_id        TEXT,
    consecutive_poll_failures INT NOT NULL DEFAULT 0,
    cancellation_reason       TEXT,
    time_to_first_value_ms    INT,
    is_deleted                BOOL NOT NULL DEFAULT false,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- STEP 2: ENABLE RLS
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- STEP 3: POLICY — SELECT
CREATE POLICY "users_select"
ON public.users
FOR SELECT
USING (
    id = auth.uid()
    AND is_deleted = false
);

-- STEP 4: POLICY — INSERT / UPDATE / DELETE
CREATE POLICY "users_insert"
ON public.users
FOR INSERT
WITH CHECK (id = auth.uid());

CREATE POLICY "users_update"
ON public.users
FOR UPDATE
USING (id = auth.uid())
WITH CHECK (id = auth.uid());

CREATE POLICY "users_delete"
ON public.users
FOR DELETE
USING (id = auth.uid());

-- STEP 5: CREATE INDEX
CREATE INDEX idx_users_email
    ON public.users (email);

CREATE INDEX idx_users_stripe
    ON public.users (stripe_customer_id);
