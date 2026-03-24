"""
app/routes/settings.py

GET  /api/v1/settings  — return current user's settings fields
PATCH /api/v1/settings — update allowed fields only (mass-assignment protected)
"""

from flask import Blueprint, g, jsonify, request
from marshmallow import ValidationError as MarshmallowValidationError

from app.extensions import supabase
from app.utils.decorators import require_auth
from app.utils.exceptions import ValidationError, ReviewNotFound
from app.schemas.settings_schema import UpdateSettingsSchema


settings_bp = Blueprint("settings", __name__)

# Fields returned by both GET and PATCH
SETTINGS_FIELDS = (
    "business_name",
    "tone_preference",
    "approval_tier",
    "plan",
    "google_connected",
    "google_status",
    "reply_count_this_month",
)


def _fetch_settings(user_id: str) -> dict:
    """Fetch the settings row for this user. Raises ReviewNotFound if missing."""
    result = supabase.from_("users").select(", ".join(SETTINGS_FIELDS)).eq("id", user_id).single().execute()
    if not result.data:
        raise ReviewNotFound()
    return result.data


@settings_bp.route("/", methods=["GET"])
@require_auth
def get_settings():
    """
    Returns the current user's settings fields.
    """
    user_id = g.current_user["id"]
    settings = _fetch_settings(user_id)
    return jsonify(settings), 200


@settings_bp.route("/", methods=["PATCH"])
@require_auth
def update_settings():
    """
    Updates allowed settings fields only.
    Unknown fields are rejected by the schema — mass assignment is prevented.
    """
    user_id = g.current_user["id"]

    schema = UpdateSettingsSchema()
    try:
        data = schema.load(request.json or {})
    except MarshmallowValidationError as e:
        raise ValidationError(fields=e.messages)

    # Strip fields that were not supplied (load_default=None means not in payload)
    updates = {k: v for k, v in data.items() if v is not None}

    if not updates:
        # Nothing to update — return current settings unchanged
        settings = _fetch_settings(user_id)
        return jsonify(settings), 200

    supabase.from_("users").update(updates).eq("id", user_id).execute()

    settings = _fetch_settings(user_id)
    return jsonify(settings), 200
