from tortoise import fields, models


class Token(models.Model):
    """令牌。"""

    id = fields.BigIntField(primary_key=True)

    user = fields.ForeignKeyField(
        "models.User",
        related_name="tokens",
        on_delete=fields.CASCADE,
    )

    value = fields.CharField(max_length=32, db_index=True)
    refresh = fields.CharField(max_length=32, db_index=True)

    expire = fields.DatetimeField()
    scope = fields.CharField(max_length=128)

    created = fields.DatetimeField(auto_now_add=True)
    updated = fields.DatetimeField(auto_now=True)

    class Meta: # type: ignore
        table = "tokens"
