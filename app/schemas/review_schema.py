from marshmallow import Schema, fields, validate


class GenerateReplySchema(Schema):
    rating = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=5),
    )
    review_text = fields.Str(
        load_default="",
        validate=validate.Length(max=2000),
    )
    reviewer_name = fields.Str(load_default=None, allow_none=True)
    google_review_id = fields.Str(load_default=None, allow_none=True)
