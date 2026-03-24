from flask import Blueprint, g, make_response, current_app

from app.extensions import supabase, limiter
from app.models.user_model import create_user, get_user_by_id
from app.schemas.auth_schema import LoginSchema, SignupSchema
from app.services.gdpr_service import anonymise_user
from app.utils.decorators import require_auth, validate_request
from app.utils.errors import build_error
from app.utils.logger import log_event

auth_bp = Blueprint("auth", __name__)


def _set_session_cookie(response, access_token: str) -> None:
    """
    Set the session_token httpOnly cookie.
    All three required flags: HttpOnly, Secure (env-dependent), SameSite=Lax.
    Secure is False in development — follows the same pattern as SESSION_COOKIE_SECURE
    already set in DevelopmentConfig (config.py).
    """
    secure = current_app.config.get("SESSION_COOKIE_SECURE", True)
    response.set_cookie(
        "session_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="Lax",
        max_age=60 * 60,  # 1 hour — matches Supabase JWT default expiry
    )


def _clear_session_cookie(response) -> None:
    """Remove the session cookie with the same flags it was set with."""
    secure = current_app.config.get("SESSION_COOKIE_SECURE", True)
    response.delete_cookie(
        "session_token",
        httponly=True,
        secure=secure,
        samesite="Lax",
    )


# ──────────────────────────────────────────────────────────────
# POST /api/v1/auth/signup
# ──────────────────────────────────────────────────────────────
@auth_bp.route("/signup", methods=["POST"])
@limiter.limit("10 per hour")
@validate_request(SignupSchema)
def signup():
    data = g.validated_data

    # Step 1: Create Supabase Auth user (auth.users table)
    try:
        auth_response = supabase.auth.sign_up(
            {
                "email": data["email"],
                "password": data["password"],
            }
        )
    except Exception:
        return build_error("EMAIL_EXISTS")

    if not auth_response.user:
        return build_error("EMAIL_EXISTS")

    user_id = auth_response.user.id

    # Step 2: Create public.users profile row
    # If this fails, clean up the orphaned auth user so login will never
    # succeed against a non-existent profile.
    try:
        user = create_user(
            user_id=user_id,
            email=data["email"],
            business_name=data["business_name"],
            business_type=data["business_type"],
            tone_preference=data.get("tone_preference", "friendly"),
        )
    except Exception:
        try:
            supabase.auth.admin.delete_user(user_id)
        except Exception:
            pass  # Best-effort cleanup — log but do not mask the original error
        return build_error("SERVER_ERROR")

    log_event("user_signup", user_id=user_id, plan="free")

    response = make_response({"user": user}, 201)
    if auth_response.session:
        _set_session_cookie(response, auth_response.session.access_token)
    return response


# ──────────────────────────────────────────────────────────────
# POST /api/v1/auth/login
# ──────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("20 per minute")
@validate_request(LoginSchema)
def login():
    data = g.validated_data

    try:
        auth_response = supabase.auth.sign_in_with_password(
            {
                "email": data["email"],
                "password": data["password"],
            }
        )
    except Exception:
        return build_error("INVALID_CREDENTIALS")

    if not auth_response.user or not auth_response.session:
        return build_error("INVALID_CREDENTIALS")

    user = get_user_by_id(auth_response.user.id)
    if not user:
        return build_error("AUTH_REQUIRED")

    response = make_response({"user": user}, 200)
    _set_session_cookie(response, auth_response.session.access_token)
    return response


# ──────────────────────────────────────────────────────────────
# POST /api/v1/auth/logout
# ──────────────────────────────────────────────────────────────
@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    response = make_response({"status": "ok"}, 200)
    _clear_session_cookie(response)
    return response


# ──────────────────────────────────────────────────────────────
# GET /api/v1/auth/me
# ──────────────────────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    return {"user": g.current_user}, 200


# ──────────────────────────────────────────────────────────────
# DELETE /api/v1/auth/account
# ──────────────────────────────────────────────────────────────
@auth_bp.route("/account", methods=["DELETE"])
@require_auth
def delete_account():
    user_id = g.current_user["id"]
    anonymise_user(user_id)
    response = make_response({"status": "deleted"}, 200)
    _clear_session_cookie(response)
    return response
