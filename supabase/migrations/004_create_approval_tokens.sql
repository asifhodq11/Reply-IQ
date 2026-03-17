-- ============================================================
-- Migration 004: approval_tokens
-- ============================================================

-- STEP 1: CREATE TABLE
CREATE TABLE public.approval_tokens (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reply_id   UUID NOT NULL REFERENCES public.replies(id),
    user_id    UUID NOT NULL REFERENCES public.users(id),
    token      TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '24 hours'),
    used       BOOL NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- STEP 2: ENABLE RLS
ALTER TABLE public.approval_tokens ENABLE ROW LEVEL SECURITY;

-- STEP 3: POLICY — SELECT
CREATE POLICY "approval_tokens_select"
ON public.approval_tokens
FOR SELECT
USING (user_id = auth.uid() AND used = FALSE);

-- STEP 4: POLICY — INSERT / UPDATE / DELETE
CREATE POLICY "approval_tokens_insert"
ON public.approval_tokens
FOR INSERT
WITH CHECK (user_id = auth.uid());

CREATE POLICY "approval_tokens_update"
ON public.approval_tokens
FOR UPDATE
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

CREATE POLICY "approval_tokens_delete"
ON public.approval_tokens
FOR DELETE
USING (user_id = auth.uid());

-- STEP 5: CREATE INDEX
CREATE UNIQUE INDEX idx_approval_tokens_token
    ON public.approval_tokens (token);

CREATE INDEX idx_approval_tokens_user_id
    ON public.approval_tokens (user_id);

CREATE INDEX idx_approval_tokens_reply_id
    ON public.approval_tokens (reply_id);
