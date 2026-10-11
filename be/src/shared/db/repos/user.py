"""Data access layer for the ``users`` table."""
import uuid

from shared.db import client, tables
from shared.models.user import User


def create_user(name: str, email: str) -> User:
    """Create a new user and persist it to DynamoDB."""
    user = User(user_id=str(uuid.uuid4()), name=name, email=email)

    table = client.get_table(tables.get_users_table_name())
    table.put_item(Item=user.dict())

    return user