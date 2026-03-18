"""Deployment policy resolver functions."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.deployment.types.policy import (
    DeploymentPolicyGQL,
    UpdateDeploymentPolicyInputGQL,
    UpdateDeploymentPolicyPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.deployment.actions.deployment_policy.upsert_deployment_policy import (
    UpsertDeploymentPolicyAction,
)


@strawberry.mutation(description="Added in 26.4.0")  # type: ignore[misc]
async def update_deployment_policy(
    input: UpdateDeploymentPolicyInputGQL,
    info: Info[StrawberryGQLContext],
) -> UpdateDeploymentPolicyPayloadGQL:
    """Update (upsert) a deployment policy for a deployment."""
    deployment_uuid = UUID(str(input.deployment_id))
    upserter = input.to_upserter(deployment_uuid)

    processor = info.context.processors.deployment
    result = await processor.upsert_deployment_policy.wait_for_complete(
        UpsertDeploymentPolicyAction(upserter=upserter)
    )

    return UpdateDeploymentPolicyPayloadGQL(
        deployment_policy=DeploymentPolicyGQL.from_data(result.data),
        created=result.created,
    )
