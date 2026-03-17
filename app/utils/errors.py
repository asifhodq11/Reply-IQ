# ============================================================
# ReplyIQ Backend — Structured Error Handling
# ============================================================

from flask import jsonify

# All known system errors locked here
ERROR_CODES = {
    'AUTH_REQUIRED':          (401, 'Authentication required.'),
    'INVALID_CREDENTIALS':    (401, 'Email or password is incorrect.'),
    'EMAIL_EXISTS':           (409, 'An account with this email already exists.'),
    'REPLY_LIMIT_REACHED':    (403, 'Monthly reply limit reached. Upgrade to continue.'),
    'REVIEW_NOT_FOUND':       (404, 'Review not found.'),
    'REPLY_NOT_FOUND':        (404, 'Reply not found.'),
    'TOKEN_INVALID':          (404, 'Approval link is invalid.'),
    'TOKEN_EXPIRED':          (410, 'Approval link has expired.'),
    'TOKEN_USED':             (409, 'This reply has already been approved.'),
    'VALIDATION_ERROR':       (400, 'Request data is invalid.'),
    'AI_SERVICE_ERROR':       (503, 'AI service temporarily unavailable. Try again shortly.'),
    'GOOGLE_POST_ERROR':      (502, 'Could not post to Google. Reply saved — will retry.'),
    'STRIPE_WEBHOOK_INVALID': (400, 'Webhook signature invalid.'),
    'RATE_LIMIT_EXCEEDED':    (429, 'Too many requests. Please slow down.'),
    'SERVER_ERROR':           (500, 'An unexpected error occurred.'),
}


def build_error(code, status=None, details=None):
    """
    Builds a consistent JSON error response shape:
    { "error": true, "code": "CODE_NAME", "message": "Human text" }
    """
    http_status, message = ERROR_CODES.get(code, (500, 'An unexpected error occurred.'))
    
    # Allow override of the HTTP status code if necessary
    if status is not None:
        http_status = status
        
    body = {
        'error': True,
        'code': code,
        'message': message
    }
    
    if details:
        body['details'] = details
        
    return jsonify(body), http_status
