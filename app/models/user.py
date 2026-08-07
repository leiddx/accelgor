from tortoise import fields, models


class User(models.Model):
    """用户信息。"""

    id = fields.BigIntField(primary_key=True)

    username = fields.CharField(max_length=64, db_index=True)
    phone = fields.CharField(max_length=20, db_index=True)
    email = fields.CharField(max_length=255, db_index=True)

    password = fields.CharField(max_length=255, db_index=True)
    salt = fields.CharField(max_length=255, db_index=True)

    scope = fields.CharField(max_length=128, default="user")

    created = fields.DatetimeField(auto_now_add=True)
    updated = fields.DatetimeField(auto_now=True)

    class Meta: # type: ignore
        table = "users"
