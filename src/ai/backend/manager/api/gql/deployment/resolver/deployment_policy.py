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
from ai.backend.manager.api.gql.utils import check_admin_only, dedent_strip
from ai.backend.manager.services.deployment.actions.deployment_policy.create_deployment_policy import (
    CreateDeploymentPolicyAction,
)
from ai.backend.manager.services.deployment.actions.deployment_policy.update_deployment_policy import (
    UpdateDeploymentPolicyAction,
)

# Mutation resolvers


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
        Added in 26.3.0.
        Create a new deployment policy for a model serving endpoint,
        specifying the deployment strategy (rolling update or blue-green)
        and its configuration.
    """),
)
async def admin_create_deployment_policy(
    input: CreateDeploymentPolicyInputGQL, info: Info[StrawberryGQLContext]
) -> CreateDeploymentPolicyPayloadGQL:
    """Create a new deployment policy for an endpoint."""
    check_admin_only()
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


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
        Added in 26.3.0.
        Update an existing deployment policy,
        allowing changes to the deployment strategy,
        strategy configuration, and rollback settings.
    """),
)
async def admin_update_deployment_policy(
    input: UpdateDeploymentPolicyInputGQL, info: Info[StrawberryGQLContext]
) -> UpdateDeploymentPolicyPayloadGQL:
    """Update an existing deployment policy."""
    check_admin_only()
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
