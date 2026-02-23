"""Deployment policy resolver functions."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.deployment.types.policy import (
    CreateDeploymentPolicyInputGQL,
    CreateDeploymentPolicyPayloadGQL,
    DeploymentPolicyGQL,
    UpdateDeploymentPolicyInputGQL,
    UpdateDeploymentPolicyPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.deployment.actions.deployment_policy.create_deployment_policy import (
    CreateDeploymentPolicyAction,
)
from ai.backend.manager.services.deployment.actions.deployment_policy.update_deployment_policy import (
    UpdateDeploymentPolicyAction,
)

# Mutation resolvers


@strawberry.mutation(description="Added in 26.3.0")  # type: ignore[misc]
async def create_deployment_policy(
    input: CreateDeploymentPolicyInputGQL, info: Info[StrawberryGQLContext]
) -> CreateDeploymentPolicyPayloadGQL:
    """Create a new deployment policy for an endpoint."""
    processor = info.context.processors.deployment
    result = await processor.create_deployment_policy.wait_for_complete(
        action=CreateDeploymentPolicyAction(
            endpoint_id=UUID(input.deployment_id),
            policy_config=input.to_policy_config(),
        )
    )
    return CreateDeploymentPolicyPayloadGQL(
        deployment_policy=DeploymentPolicyGQL.from_data(result.data)
    )


@strawberry.mutation(description="Added in 26.3.0")  # type: ignore[misc]
async def update_deployment_policy(
    input: UpdateDeploymentPolicyInputGQL, info: Info[StrawberryGQLContext]
) -> UpdateDeploymentPolicyPayloadGQL:
    """Update an existing deployment policy."""
    processor = info.context.processors.deployment
    result = await processor.update_deployment_policy.wait_for_complete(
        action=UpdateDeploymentPolicyAction(
            policy_id=UUID(input.id),
            updater_spec=input.to_updater_spec(),
        )
    )
    return UpdateDeploymentPolicyPayloadGQL(
        deployment_policy=DeploymentPolicyGQL.from_data(result.data)
    )
