"""Deployment policy resolver functions."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.deployment.types.policy import (
    DeploymentPolicyGQL,
    UpdateDeploymentPolicyInputGQL,
    UpdateDeploymentPolicyPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only, dedent_strip
from ai.backend.manager.services.deployment.actions.deployment_policy.upsert_deployment_policy import (
    UpsertDeploymentPolicyAction,
)


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
        Added in 26.4.0.
        Create or update the deployment policy for a given deployment (upsert semantics).
        If the deployment already has a policy, it is replaced entirely with the new configuration.
    """),
)
async def update_deployment_policy(
    input: UpdateDeploymentPolicyInputGQL,
    info: Info[StrawberryGQLContext],
) -> UpdateDeploymentPolicyPayloadGQL:
    """Update (upsert) a deployment policy for a deployment."""
    check_admin_only()
    upserter = input.to_upserter()

    processor = info.context.processors.deployment
    result = await processor.upsert_deployment_policy.wait_for_complete(
        UpsertDeploymentPolicyAction(upserter=upserter)
    )

    return UpdateDeploymentPolicyPayloadGQL(
        deployment_policy=DeploymentPolicyGQL.from_data(result.data),
    )
