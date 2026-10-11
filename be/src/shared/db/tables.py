"""Table name resolution from environment variables."""
import os


def get_users_table_name() -> str:
    """Return the name of the ``users`` table, overridable via ``USERS_TABLE``."""
    return os.environ.get("USERS_TABLE", "users")