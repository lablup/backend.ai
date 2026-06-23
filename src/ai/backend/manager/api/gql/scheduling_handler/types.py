"""GraphQL types for the scheduling-handler registry."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.scheduling_handler.types import SchedulingHandlerNode
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

__all__ = (
    "SchedulingHandlerCategoryGQL",
    "SchedulingHandlerNodeGQL",
)


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Category of a deployment scheduling handler (lifecycle/scaling/health).",
    ),
    name="SchedulingHandlerCategory",
)
class SchedulingHandlerCategoryGQL(StrEnum):
    """Handler category mirroring the data-layer enum values."""

    LIFECYCLE = "lifecycle"
    SCALING = "scaling"
    HEALTH = "health"


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description=(
            "Metadata for a single registered deployment scheduling handler. "
            "Surfaces the stable ``name`` used in ``DeploymentOptions.handler_options.by_handler``."
        ),
    ),
    model=SchedulingHandlerNode,
    all_fields=True,
    name="SchedulingHandlerNode",
)
class SchedulingHandlerNodeGQL(PydanticOutputMixin[SchedulingHandlerNode]):
    """GraphQL wrapper for :class:`SchedulingHandlerNode`."""

    pass
