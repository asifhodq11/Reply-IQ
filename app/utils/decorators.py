from functools import wraps

from flask import g, request
from marshmallow import ValidationError

from app.extensions import supabase
from app.models.user_model import get_user_by_id
from app.utils.errors import build_error
from app.utils.exceptions import AuthRequired


def require_auth(f):
    """
    Reads the JWT from the session_token httpOnly cookie.
    Verifies it with Supabase, then fetches the public.users profile row.
    Injects g.current_user on success.
    Returns 401 AUTH_REQUIRED on any failure — never 403.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("session_token")
        if not token:
            raise AuthRequired()

        try:
            user_response = supabase.auth.get_user(token)
            user_id = user_response.user.id
        except Exception:
            raise AuthRequired()

        user = get_user_by_id(user_id)
        if not user or user.get("is_deleted"):
            raise AuthRequired()

        g.current_user = user
        return f(*args, **kwargs)

    return decorated


def validate_request(schema_class):
    """
    Validates request.json against the given Marshmallow schema.
    Injects g.validated_data on success.
    Returns 400 VALIDATION_ERROR with field-level error details on failure.
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            schema = schema_class()
            try:
                g.validated_data = schema.load(request.json or {})
            except ValidationError as e:
                return build_error("VALIDATION_ERROR", details=e.messages)
            return f(*args, **kwargs)

        return decorated

    return decorator
