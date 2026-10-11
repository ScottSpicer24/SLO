"""Custom exceptions for the data access layer."""


class DatabaseError(Exception):
    """Base class for database-related exceptions."""


class RecordNotFoundError(DatabaseError):
    """Raised when a requested record does not exist."""


class RecordAlreadyExistsError(DatabaseError):
    """Raised when inserting a record with a duplicate key."""