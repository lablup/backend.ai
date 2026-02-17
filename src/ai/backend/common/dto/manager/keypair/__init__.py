"""
Common DTOs for keypair system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    ActivateKeyPairRequest,
    CreateKeyPairRequest,
    DeactivateKeyPairRequest,
    DeleteKeyPairRequest,
    KeyPairFilter,
    KeyPairOrder,
    SearchKeyPairsRequest,
    StringFilter,
    UpdateKeyPairRequest,
)
from .response import (
    CreateKeyPairResponse,
    DeleteKeyPairResponse,
    GetKeyPairResponse,
    KeyPairDTO,
    PaginationInfo,
    SearchKeyPairsResponse,
    UpdateKeyPairResponse,
)
from .types import (
    KeyPairOrderField,
    OrderDirection,
)

__all__ = (
    # Types
    "OrderDirection",
    "KeyPairOrderField",
    # Request DTOs
    "CreateKeyPairRequest",
    "UpdateKeyPairRequest",
    "SearchKeyPairsRequest",
    "DeleteKeyPairRequest",
    "ActivateKeyPairRequest",
    "DeactivateKeyPairRequest",
    "StringFilter",
    "KeyPairFilter",
    "KeyPairOrder",
    # Response DTOs
    "KeyPairDTO",
    "CreateKeyPairResponse",
    "GetKeyPairResponse",
    "SearchKeyPairsResponse",
    "UpdateKeyPairResponse",
    "DeleteKeyPairResponse",
    "PaginationInfo",
)
