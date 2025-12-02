"""
App Proxy Worker error classes.
"""

from .circuit import (
    InvalidAppInfoTypeError,
    InvalidCircuitDataError,
    InvalidFrontendTypeError,
)
from .config import (
    CleanupContextNotInitializedError,
    MissingAnnounceAddressError,
    MissingPortConfigError,
    MissingPortProxyConfigError,
    MissingProfilingConfigError,
    MissingTraefikConfigError,
)
from .process import (
    InvalidMatrixSizeError,
    SubprocessPipeError,
)

__all__ = [
    # circuit
    "InvalidAppInfoTypeError",
    "InvalidCircuitDataError",
    "InvalidFrontendTypeError",
    # config
    "CleanupContextNotInitializedError",
    "MissingAnnounceAddressError",
    "MissingPortConfigError",
    "MissingPortProxyConfigError",
    "MissingProfilingConfigError",
    "MissingTraefikConfigError",
    # process
    "InvalidMatrixSizeError",
    "SubprocessPipeError",
]
