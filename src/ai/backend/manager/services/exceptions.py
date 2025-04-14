from ai.backend.common.exception import BackendError


class BaseServiceException(BackendError):
    """Base exception for all service-related errors."""
