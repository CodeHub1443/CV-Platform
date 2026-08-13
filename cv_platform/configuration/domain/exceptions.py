class ConfigurationError(Exception):
    """Base exception for the Configuration Platform."""


class ValidationError(ConfigurationError, ValueError):
    """Input data failed domain validation."""


class NotFoundError(ConfigurationError, LookupError):
    """Requested entity does not exist."""


class ConflictError(ConfigurationError):
    """Operation conflicts with current entity state or relationships."""


class OptimisticLockError(ConflictError):
    """Entity was modified concurrently; caller must retry with the latest version."""
