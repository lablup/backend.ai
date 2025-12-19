"""GraphQL mutations for revision activation operations."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.common.exception import ModelDeploymentUnavailable
from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.deployment.actions.revision_operations import (
    ActivateRevisionAction,
)

from .model_deployment import ModelDeployment


@strawberry.input(
    name="ActivateRevisionInput",
    description="Added in 25.19.0. Input for activating a revision to be the current revision.",
)
class ActivateRevisionInputGQL:
    deployment_id: ID
    revision_id: ID


@strawberry.type(
    name="ActivateRevisionPayload",
    description="Added in 25.19.0. Result of activating a revision.",
)
class ActivateRevisionPayloadGQL:
    deployment: ModelDeployment
    previous_revision_id: Optional[ID]
    activated_revision_id: ID


@strawberry.mutation(
    description="Added in 25.19.0. Activate a specific revision to be the current revision."
)
async def activate_deployment_revision(
    input: ActivateRevisionInputGQL,
    info: Info[StrawberryGQLContext, None],
) -> ActivateRevisionPayloadGQL:
    """Activate a revision to be the current revision for a deployment."""
    _, deployment_id = resolve_global_id(input.deployment_id)
    _, revision_id = resolve_global_id(input.revision_id)

    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )

    result = await processor.activate_revision.wait_for_complete(
        ActivateRevisionAction(
            deployment_id=UUID(deployment_id),
            revision_id=UUID(revision_id),
        )
    )

    return ActivateRevisionPayloadGQL(
        deployment=ModelDeployment.from_dataclass(result.deployment),
        previous_revision_id=(
            ID(str(result.previous_revision_id)) if result.previous_revision_id else None
        ),
        activated_revision_id=ID(str(result.activated_revision_id)),
    )
