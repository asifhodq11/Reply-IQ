from marshmallow import Schema, fields, validate


class SignupSchema(Schema):
    email = fields.Email(
        required=True, error_messages={"required": "Email is required.", "invalid": "Enter a valid email address."}
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=8, error="Password must be at least 8 characters."),
        error_messages={"required": "Password is required."},
    )
    business_name = fields.String(
        required=True,
        validate=validate.Length(min=1, error="Business name cannot be blank."),
        error_messages={"required": "Business name is required."},
    )
    business_type = fields.String(
        required=True,
        validate=validate.Length(min=1, error="Business type cannot be blank."),
        error_messages={"required": "Business type is required."},
    )
    # Optional — database default is 'friendly'
    tone_preference = fields.String(
        load_default="friendly",
        validate=validate.OneOf(
            ["friendly", "formal", "casual"], error="tone_preference must be one of: friendly, formal, casual."
        ),
    )


class LoginSchema(Schema):
    email = fields.Email(
        required=True, error_messages={"required": "Email is required.", "invalid": "Enter a valid email address."}
    )
    password = fields.String(required=True, error_messages={"required": "Password is required."})
