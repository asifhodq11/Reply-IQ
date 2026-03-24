-- 007_add_increment_rpc.sql
-- Atomic increment for user replies. SECURITY DEFINER bypasses RLS safely 
-- because the parameter matches the ID being updated.

CREATE OR REPLACE FUNCTION public.increment_reply_count(user_id_input UUID)
RETURNS void AS $$
  UPDATE public.users 
  SET reply_count_this_month = reply_count_this_month + 1
  WHERE id = user_id_input;
$$ LANGUAGE sql SECURITY DEFINER SET search_path = public;
