"""
Common DTOs for group (project) system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    RegistryQuotaReadRequest,
    RegistryQuotaRequest,
)
from .response import (
    RegistryQuotaReadResponse,
)

__all__ = (
    # Request DTOs
    "RegistryQuotaRequest",
    "RegistryQuotaReadRequest",
    # Response DTOs
    "RegistryQuotaReadResponse",
)
