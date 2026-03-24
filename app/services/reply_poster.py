"""
app/services/reply_poster.py

Handles posting approved or auto-approved review replies
out to the external platform (e.g. Google Business Profile).
"""

from app.extensions import supabase
from app.utils.exceptions import GooglePostError


def post_reply_to_google(reply_id: str, user_id: str) -> bool:
    """
    Posts a review reply to Google Business Profile.
    Includes a strict duplicate check to prevent double-posting
    the same reply if tokens are somehow double-clicked or racily approved.

    Returns:
        True: if successfully posted
        False: if a reply was already posted for this review
    Raises:
        GooglePostError: if the external API call fails
    """
    # 1. Get the review_id to check for duplicates
    reply_res = supabase.from_("replies").select("review_id").eq("id", reply_id).eq("user_id", user_id).execute()

    if not reply_res.data:
        raise GooglePostError(review_id=None, google_error="Reply not found or unauthorized access.")

    review_id = reply_res.data[0]["review_id"]

    # 2. Prevent duplicate posting on the same review
    existing_res = (
        supabase.from_("replies")
        .select("id")
        .eq("review_id", review_id)
        .in_("status", ["posted", "auto-posted"])
        .execute()
    )

    if existing_res.data:
        # A reply has already been posted to Google for this review
        return False

    # 3. Post to Google API
    # TODO Phase 8 — wire up real Google API call

    # 4. Mark the reply as successfully posted
    supabase.from_("replies").update({"status": "posted"}).eq("id", reply_id).eq("user_id", user_id).execute()

    return True
