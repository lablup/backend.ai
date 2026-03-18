"""
Domain DTO v2 models for Manager API.
"""

from ai.backend.common.dto.manager.v2.domain.request import (
    CreateDomainInput,
    DeleteDomainInput,
    DomainFilter,
    DomainOrder,
    PurgeDomainInput,
    SearchDomainsRequest,
    UpdateDomainInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DeleteDomainPayload,
    DomainBasicInfo,
    DomainLifecycleInfo,
    DomainNode,
    DomainPayload,
    DomainRegistryInfo,
    PurgeDomainPayload,
    SearchDomainsPayload,
)
from ai.backend.common.dto.manager.v2.domain.types import (
    DomainOrderField,
    OrderDirection,
)

__all__ = (
    # Request DTOs
    "CreateDomainInput",
    "UpdateDomainInput",
    "DeleteDomainInput",
    "PurgeDomainInput",
    "DomainFilter",
    "DomainOrder",
    "SearchDomainsRequest",
    # Response DTOs
    "DomainBasicInfo",
    "DomainRegistryInfo",
    "DomainLifecycleInfo",
    "DomainNode",
    "DomainPayload",
    "SearchDomainsPayload",
    "DeleteDomainPayload",
    "PurgeDomainPayload",
    # Types
    "DomainOrderField",
    "OrderDirection",
)
