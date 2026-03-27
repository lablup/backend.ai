"""
Model Serving DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.model_serving.request import (
    CreateServiceInput,
    DeleteServiceInput,
    GenerateTokenInput,
    ScaleServiceInput,
    ServiceConfigInput,
    UpdateServiceInput,
)
from ai.backend.common.dto.manager.v2.model_serving.response import (
    CompactServiceNode,
    CreateServicePayload,
    DeleteServicePayload,
    GenerateTokenPayload,
    ScaleServicePayload,
    ServiceNode,
    UpdateServicePayload,
)
from ai.backend.common.dto.manager.v2.model_serving.types import (
    EndpointLifecycle,
    OrderDirection,
    RouteInfoSummary,
    RuntimeVariant,
    ServiceOrderField,
)

__all__ = (
    # Types
    "EndpointLifecycle",
    "OrderDirection",
    "RouteInfoSummary",
    "RuntimeVariant",
    "ServiceOrderField",
    # Input models (request)
    "CreateServiceInput",
    "DeleteServiceInput",
    "GenerateTokenInput",
    "ScaleServiceInput",
    "ServiceConfigInput",
    "UpdateServiceInput",
    # Node and Payload models (response)
    "CompactServiceNode",
    "CreateServicePayload",
    "DeleteServicePayload",
    "GenerateTokenPayload",
    "ScaleServicePayload",
    "ServiceNode",
    "UpdateServicePayload",
)
