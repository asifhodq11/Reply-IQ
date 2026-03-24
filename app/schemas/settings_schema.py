# ============================================================
# ReplyIQ Backend — Settings Update Schema
# ============================================================

from marshmallow import Schema, fields, validate, RAISE


class UpdateSettingsSchema(Schema):
    """
    Validates a PATCH /settings request body.
    All fields are optional — any subset may be updated.
    Unknown fields are REJECTED to prevent mass assignment.
    """

    business_name = fields.String(
        load_default=None,
        validate=validate.Length(min=1),
    )

    tone_preference = fields.String(
        load_default=None,
        validate=validate.OneOf(["friendly", "formal", "casual"]),
    )

    approval_tier = fields.Integer(
        load_default=None,
        validate=validate.OneOf([1, 2, 3]),
    )

    class Meta:
        unknown = RAISE
