from app.extensions import supabase


def create_user(
    user_id: str,
    email: str,
    business_name: str,
    business_type: str,
    tone_preference: str = "friendly",
) -> dict:
    """
    Insert a new row into public.users after Supabase Auth creates the
    auth.users entry. Called once per signup — never called again.

    Only the non-defaulted columns are written here. The database supplies
    defaults for: plan, reply_count_this_month, billing_cycle_start,
    approval_tier, google_connected, google_status, consecutive_poll_failures,
    is_deleted, created_at.

    Raises on any Supabase error — the caller (auth route) is responsible
    for catching and cleaning up the orphaned auth user.
    """
    result = (
        supabase.table("users")
        .insert(
            {
                "id": user_id,
                "email": email,
                "business_name": business_name,
                "business_type": business_type,
                "tone_preference": tone_preference,
            }
        )
        .execute()
    )
    return result.data[0]


def get_user_by_id(user_id: str) -> dict | None:
    """
    Fetch one non-deleted user row by primary key.

    The users table uses id as both PK and user anchor — querying
    .eq('id', user_id) is the equivalent of the user_id filter required
    by Rule 3 for all other tables.

    Returns None if the user does not exist or is soft-deleted.
    """
    result = supabase.table("users").select("*").eq("id", user_id).eq("is_deleted", False).maybe_single().execute()
    return result.data
