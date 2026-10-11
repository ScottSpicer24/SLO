"""Data model for the ``users`` table."""
from dataclasses import asdict, dataclass


@dataclass
class User:
    user_id: str
    name: str
    email: str
    status: str = "active"

    def dict(self) -> dict:
        return asdict(self)