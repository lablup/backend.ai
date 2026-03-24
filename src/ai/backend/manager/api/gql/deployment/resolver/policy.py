"""Deployment policy resolver functions."""

from __future__ import annotations

from strawberry import Info

from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.deployment.types.policy import (
    DeploymentPolicyGQL,
    UpdateDeploymentPolicyInputGQL,
    UpdateDeploymentPolicyPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.0",
        description="Create or update the deployment policy for a given deployment (upsert semantics). If the deployment already has a policy, it is replaced entirely with the new configuration",
    )
)  # type: ignore[misc]
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
