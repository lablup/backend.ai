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
    payload = await info.context.adapters.deployment.upsert_policy(input.to_pydantic())
    return UpdateDeploymentPolicyPayloadGQL(
        deployment_policy=DeploymentPolicyGQL.from_pydantic(payload.policy),
    )
