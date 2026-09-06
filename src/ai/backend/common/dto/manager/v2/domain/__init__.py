"""
Domain DTO v2 models for Manager API.
"""

from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    CreateDomainInput,
    DeleteDomainInput,
    DomainFilter,
    DomainOrder,
    PurgeDomainInput,
    RestoreDomainInput,
    SearchDomainsRequest,
    UpdateDomainInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    AdminSearchDomainsPayload,
    DeleteDomainPayload,
    DomainBasicInfo,
    DomainLifecycleInfo,
    DomainNode,
    DomainPayload,
    DomainRegistryInfo,
    PurgeDomainPayload,
    RestoreDomainPayload,
    SearchDomainsPayload,
)
from ai.backend.common.dto.manager.v2.domain.types import (
    DomainFairShareScopeDTO,
    DomainOrderField,
    DomainProjectFilter,
    DomainUsageScopeDTO,
    DomainUserFilter,
    OrderDirection,
)

__all__ = (
    # Request DTOs
    "AdminSearchDomainsInput",
    "CreateDomainInput",
    "UpdateDomainInput",
    "DeleteDomainInput",
    "RestoreDomainInput",
    "PurgeDomainInput",
    "DomainFilter",
    "DomainOrder",
    "SearchDomainsRequest",
    # Response DTOs
    "AdminSearchDomainsPayload",
    "DomainBasicInfo",
    "DomainRegistryInfo",
    "DomainLifecycleInfo",
    "DomainNode",
    "DomainPayload",
    "SearchDomainsPayload",
    "DeleteDomainPayload",
    "RestoreDomainPayload",
    "PurgeDomainPayload",
    # Types
    "DomainFairShareScopeDTO",
    "DomainOrderField",
    "DomainProjectFilter",
    "DomainUsageScopeDTO",
    "DomainUserFilter",
    "OrderDirection",
)
