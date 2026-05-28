"""
App Proxy Worker error classes.
"""

from .circuit import (
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
    SubprocessPipeError,
)

__all__ = [
    # circuit
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
    "SubprocessPipeError",
]
