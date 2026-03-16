"""
Quota Scope DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.quota_scope.request import (
    QuotaScopeFilter,
    QuotaScopeOrder,
    SearchQuotaScopesInput,
    SetQuotaInput,
    UnsetQuotaInput,
)
from ai.backend.common.dto.manager.v2.quota_scope.response import (
    GetQuotaScopePayload,
    QuotaScopeNode,
    SearchQuotaScopesPayload,
    SetQuotaPayload,
    UnsetQuotaPayload,
)
from ai.backend.common.dto.manager.v2.quota_scope.types import (
    OrderDirection,
    QuotaScopeOrderField,
)

__all__ = (
    # Types
    "OrderDirection",
    "QuotaScopeOrderField",
    # Input models (request)
    "QuotaScopeFilter",
    "QuotaScopeOrder",
    "SearchQuotaScopesInput",
    "SetQuotaInput",
    "UnsetQuotaInput",
    # Node and Payload models (response)
    "GetQuotaScopePayload",
    "QuotaScopeNode",
    "SearchQuotaScopesPayload",
    "SetQuotaPayload",
    "UnsetQuotaPayload",
)
