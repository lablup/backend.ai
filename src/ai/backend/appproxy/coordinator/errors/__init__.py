"""
App Proxy Coordinator error classes.
"""

from .circuit import (
    CircuitCreationError,
    InvalidCircuitConfigError,
    InvalidCircuitStateError,
)
from .config import (
    CleanupContextNotInitializedError,
    InvalidEnumTypeError,
    InvalidSessionParameterError,
    InvalidURLError,
    LockContextNotInitializedError,
    MissingConfigFileError,
    MissingDatabaseURLError,
    MissingFrontendConfigError,
    MissingHealthCheckInfoError,
    MissingProfilingConfigError,
    MissingRouteInfoError,
    MissingTraefikConfigError,
    TransactionResultError,
)

__all__ = [
    # circuit
    "CircuitCreationError",
    "InvalidCircuitConfigError",
    "InvalidCircuitStateError",
    # config
    "CleanupContextNotInitializedError",
    "InvalidEnumTypeError",
    "InvalidSessionParameterError",
    "InvalidURLError",
    "LockContextNotInitializedError",
    "MissingConfigFileError",
    "MissingDatabaseURLError",
    "MissingFrontendConfigError",
    "MissingHealthCheckInfoError",
    "MissingProfilingConfigError",
    "MissingRouteInfoError",
    "MissingTraefikConfigError",
    "TransactionResultError",
]
