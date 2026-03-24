# ============================================================
# ReplyIQ Backend — Custom Exception Hierarchy
# ============================================================
#
# All domain exceptions inherit from ReplyIQError.
# The global handler in app/__init__.py catches ReplyIQError
# and converts it to a structured JSON response automatically.
# Never catch these in routes — let them bubble to the handler.
# ============================================================


class ReplyIQError(Exception):
    """Base class for all ReplyIQ domain exceptions."""

    error_code = "SERVER_ERROR"
    http_status = 500

    def __init__(self, details=None):
        super().__init__(self.error_code)
        self.details = details


# ── Auth exceptions ─────────────────────────────────────────


class AuthRequired(ReplyIQError):
    error_code = "AUTH_REQUIRED"
    http_status = 401


class InvalidCredentials(ReplyIQError):
    error_code = "INVALID_CREDENTIALS"
    http_status = 401


class EmailExists(ReplyIQError):
    error_code = "EMAIL_EXISTS"
    http_status = 409


class PlanRequired(ReplyIQError):
    """Raised when an action requires a paid plan."""

    error_code = "PLAN_REQUIRED"
    http_status = 403

    def __init__(self, required_plan="starter"):
        super().__init__(details={"required_plan": required_plan})


# ── Usage exceptions ─────────────────────────────────────────


class ReplyLimitReached(ReplyIQError):
    """Raised when the user has exhausted their monthly reply quota."""

    error_code = "REPLY_LIMIT_REACHED"
    http_status = 403

    def __init__(self, used=None, limit=None, reset_date=None):
        super().__init__(
            details={
                "replies_used": used,
                "replies_limit": limit,
                "reset_date": reset_date,
            }
        )


# ── Resource exceptions ──────────────────────────────────────


class ReviewNotFound(ReplyIQError):
    error_code = "REVIEW_NOT_FOUND"
    http_status = 404


class ReplyNotFound(ReplyIQError):
    error_code = "REPLY_NOT_FOUND"
    http_status = 404


# ── Token exceptions ─────────────────────────────────────────


class TokenInvalid(ReplyIQError):
    error_code = "TOKEN_INVALID"
    http_status = 404


class TokenExpired(ReplyIQError):
    error_code = "TOKEN_EXPIRED"
    http_status = 410


class TokenAlreadyUsed(ReplyIQError):
    error_code = "TOKEN_USED"
    http_status = 409


# ── External service exceptions ──────────────────────────────


class ValidationError(ReplyIQError):
    """Raised for application-level validation failures (not Marshmallow)."""

    error_code = "VALIDATION_ERROR"
    http_status = 400

    def __init__(self, fields=None, message=None):
        super().__init__(details={"fields": fields or {}, "message": message})


class AIServiceError(ReplyIQError):
    """Raised when an AI provider call fails after all retries."""

    error_code = "AI_SERVICE_ERROR"
    http_status = 503

    def __init__(self, attempt=None, model=None):
        super().__init__(
            details={
                "attempt": attempt,
                "model": model,
            }
        )


class GooglePostError(ReplyIQError):
    """Raised when posting a reply to Google fails."""

    error_code = "GOOGLE_POST_ERROR"
    http_status = 502

    def __init__(self, review_id=None, google_error=None):
        super().__init__(
            details={
                "review_id": review_id,
                "google_error": google_error,
                "note": "Reply saved as draft — will retry automatically.",
            }
        )


class StripeWebhookInvalid(ReplyIQError):
    error_code = "STRIPE_WEBHOOK_INVALID"
    http_status = 400


class RateLimitExceeded(ReplyIQError):
    error_code = "RATE_LIMIT_EXCEEDED"
    http_status = 429
