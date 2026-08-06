from tortoise import fields, models


class User(models.Model):
    """用户信息。"""

    id = fields.BigIntField(pk=True)

    username = fields.CharField(max_length=64, index=True)
    phone = fields.CharField(max_length=20, index=True)
    email = fields.CharField(max_length=255, index=True)

    password = fields.CharField(max_length=255, index=True)
    salt = fields.CharField(max_length=255, index=True)

    scope = fields.CharField(max_length=128)

    created = fields.DatetimeField(auto_now_add=True)
    updated = fields.DatetimeField(auto_now=True)

    class Meta: # type: ignore
        table = "users"
