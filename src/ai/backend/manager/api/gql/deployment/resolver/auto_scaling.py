"""Auto-scaling rule resolver functions."""

from __future__ import annotations

import strawberry
from strawberry import ID, Info

from ai.backend.manager.api.gql.deployment.types.auto_scaling import (
    AutoScalingRule,
    CreateAutoScalingRuleInput,
    CreateAutoScalingRulePayload,
    DeleteAutoScalingRuleInput,
    DeleteAutoScalingRulePayload,
    UpdateAutoScalingRuleInput,
    UpdateAutoScalingRulePayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

# Mutation resolvers


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def create_auto_scaling_rule(
    input: CreateAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> CreateAutoScalingRulePayload:
    """Create a new auto-scaling rule for a deployment."""
    payload = await info.context.adapters.deployment.create_rule(input.to_pydantic())
    return CreateAutoScalingRulePayload(rule=AutoScalingRule.from_pydantic(payload.rule))


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def update_auto_scaling_rule(
    input: UpdateAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> UpdateAutoScalingRulePayload:
    """Update an existing auto-scaling rule."""
    payload = await info.context.adapters.deployment.update_rule(input.to_pydantic())
    return UpdateAutoScalingRulePayload(rule=AutoScalingRule.from_pydantic(payload.rule))


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def delete_auto_scaling_rule(
    input: DeleteAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> DeleteAutoScalingRulePayload:
    """Delete an auto-scaling rule."""
    payload = await info.context.adapters.deployment.delete_rule(input.to_pydantic())
    return DeleteAutoScalingRulePayload(id=ID(str(payload.id)))
