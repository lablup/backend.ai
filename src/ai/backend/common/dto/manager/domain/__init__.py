"""
Common DTOs for domain management used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    CreateDomainRequest,
    DeleteDomainRequest,
    DomainFilter,
    PurgeDomainRequest,
    SearchDomainsRequest,
    UpdateDomainRequest,
)
from .response import (
    CreateDomainResponse,
    DeleteDomainResponse,
    DomainDTO,
    GetDomainResponse,
    PaginationInfo,
    PurgeDomainResponse,
    SearchDomainsResponse,
    UpdateDomainResponse,
)
from .types import (
    DomainOrder,
    DomainOrderField,
    OrderDirection,
)

__all__ = (
    # Types
    "DomainOrder",
    "DomainOrderField",
    "OrderDirection",
    # Request DTOs
    "CreateDomainRequest",
    "UpdateDomainRequest",
    "SearchDomainsRequest",
    "DomainFilter",
    "DeleteDomainRequest",
    "PurgeDomainRequest",
    # Response DTOs
    "DomainDTO",
    "CreateDomainResponse",
    "GetDomainResponse",
    "SearchDomainsResponse",
    "UpdateDomainResponse",
    "DeleteDomainResponse",
    "PurgeDomainResponse",
    "PaginationInfo",
)
