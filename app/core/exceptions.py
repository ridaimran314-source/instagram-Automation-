"""Application-level exceptions."""


class AppError(Exception):
    """Base exception for application-specific errors."""


class ConfigurationError(AppError):
    """Raised when required configuration is missing or invalid."""


class ServiceInitializationError(AppError):
    """Raised when a startup dependency cannot be initialized."""


class ExternalServiceError(AppError):
    """Raised when an external provider call fails."""


class DataMappingError(AppError):
    """Raised when third-party data cannot be mapped safely."""
