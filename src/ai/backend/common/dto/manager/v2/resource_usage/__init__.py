"""Resource Usage DTOs v2 for Manager API."""

from ai.backend.common.dto.manager.v2.resource_usage.request import (
    AdminSearchDomainUsageBucketsInput,
    AdminSearchProjectUsageBucketsInput,
    AdminSearchUserUsageBucketsInput,
    DomainSearchDomainUsageBucketsInput,
    DomainSearchProjectUsageBucketsInput,
    DomainSearchUserUsageBucketsInput,
    DomainUsageBucketFilter,
    DomainUsageBucketOrderBy,
    ProjectUsageBucketFilter,
    ProjectUsageBucketOrderBy,
    UserUsageBucketFilter,
    UserUsageBucketOrderBy,
)
from ai.backend.common.dto.manager.v2.resource_usage.response import (
    AdminSearchDomainUsageBucketsPayload,
    AdminSearchProjectUsageBucketsPayload,
    AdminSearchUserUsageBucketsPayload,
    DomainSearchDomainUsageBucketsPayload,
    DomainSearchProjectUsageBucketsPayload,
    DomainSearchUserUsageBucketsPayload,
    DomainUsageBucketNode,
    ProjectUsageBucketNode,
    UserUsageBucketNode,
)
from ai.backend.common.dto.manager.v2.resource_usage.types import (
    OrderDirection,
    UsageBucketOrderField,
)

__all__ = (
    # Request
    "AdminSearchDomainUsageBucketsInput",
    "AdminSearchProjectUsageBucketsInput",
    "AdminSearchUserUsageBucketsInput",
    "DomainSearchDomainUsageBucketsInput",
    "DomainSearchProjectUsageBucketsInput",
    "DomainSearchUserUsageBucketsInput",
    "DomainUsageBucketFilter",
    "DomainUsageBucketOrderBy",
    "ProjectUsageBucketFilter",
    "ProjectUsageBucketOrderBy",
    "UserUsageBucketFilter",
    "UserUsageBucketOrderBy",
    # Response nodes
    "DomainUsageBucketNode",
    "ProjectUsageBucketNode",
    "UserUsageBucketNode",
    # Response payloads
    "AdminSearchDomainUsageBucketsPayload",
    "AdminSearchProjectUsageBucketsPayload",
    "AdminSearchUserUsageBucketsPayload",
    "DomainSearchDomainUsageBucketsPayload",
    "DomainSearchProjectUsageBucketsPayload",
    "DomainSearchUserUsageBucketsPayload",
    # Types
    "OrderDirection",
    "UsageBucketOrderField",
)
