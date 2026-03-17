-- ============================================================
-- Migration 003: replies
-- ============================================================

-- STEP 1: CREATE TABLE
CREATE TABLE public.replies (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id     UUID NOT NULL REFERENCES public.reviews(id),
    user_id       UUID NOT NULL REFERENCES public.users(id),
    reply_text    TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'draft',
    was_edited    BOOL NOT NULL DEFAULT false,
    posted_at     TIMESTAMPTZ,
    tokens_used   INT,
    generation_ms INT,
    model_used    TEXT,
    is_deleted    BOOL NOT NULL DEFAULT false,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- STEP 2: ENABLE RLS
ALTER TABLE public.replies ENABLE ROW LEVEL SECURITY;

-- STEP 3: POLICY — SELECT
CREATE POLICY "replies_select"
ON public.replies
FOR SELECT
USING (
    user_id = auth.uid()
    AND is_deleted = false
);

-- STEP 4: POLICY — INSERT / UPDATE / DELETE
CREATE POLICY "replies_insert"
ON public.replies
FOR INSERT
WITH CHECK (user_id = auth.uid());

CREATE POLICY "replies_update"
ON public.replies
FOR UPDATE
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

CREATE POLICY "replies_delete"
ON public.replies
FOR DELETE
USING (user_id = auth.uid());

-- STEP 5: CREATE INDEX
CREATE INDEX idx_replies_user_id
    ON public.replies (user_id);

CREATE INDEX idx_replies_review_id
    ON public.replies (review_id);

CREATE INDEX idx_replies_status
    ON public.replies (user_id, status);
