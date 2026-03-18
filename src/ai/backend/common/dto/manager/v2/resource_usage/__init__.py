"""Resource Usage DTOs v2 for Manager API."""

from ai.backend.common.dto.manager.v2.resource_usage.request import (
    AdminSearchDomainUsageBucketsInput,
    AdminSearchProjectUsageBucketsInput,
    AdminSearchUserUsageBucketsInput,
    DomainSearchDomainUsageBucketsInput,
    DomainSearchProjectUsageBucketsInput,
    DomainSearchUserUsageBucketsInput,
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

__all__ = (
    # Request
    "AdminSearchDomainUsageBucketsInput",
    "AdminSearchProjectUsageBucketsInput",
    "AdminSearchUserUsageBucketsInput",
    "DomainSearchDomainUsageBucketsInput",
    "DomainSearchProjectUsageBucketsInput",
    "DomainSearchUserUsageBucketsInput",
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
)
