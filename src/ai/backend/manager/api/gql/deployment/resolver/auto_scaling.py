"""Auto-scaling rule resolver functions."""

from __future__ import annotations

from uuid import UUID

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
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.create_auto_scaling_rule import (
    CreateAutoScalingRuleAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.delete_auto_scaling_rule import (
    DeleteAutoScalingRuleAction,
)

# Mutation resolvers


@strawberry.mutation(description="Added in 25.16.0")
async def create_auto_scaling_rule(
    input: CreateAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> CreateAutoScalingRulePayload:
    """Create a new auto-scaling rule for a deployment."""
    processor = info.context.processors.deployment
    result = await processor.create_auto_scaling_rule.wait_for_complete(
        action=CreateAutoScalingRuleAction(input.to_creator())
    )
    return CreateAutoScalingRulePayload(
        auto_scaling_rule=AutoScalingRule.from_dataclass(result.data)
    )


@strawberry.mutation(description="Added in 25.16.0")
async def update_auto_scaling_rule(
    input: UpdateAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> UpdateAutoScalingRulePayload:
    """Update an existing auto-scaling rule."""
    processor = info.context.processors.deployment
    action_result = await processor.update_auto_scaling_rule.wait_for_complete(input.to_action())
    return UpdateAutoScalingRulePayload(
        auto_scaling_rule=AutoScalingRule.from_dataclass(action_result.data)
    )


@strawberry.mutation(description="Added in 25.16.0")
async def delete_auto_scaling_rule(
    input: DeleteAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> DeleteAutoScalingRulePayload:
    """Delete an auto-scaling rule."""
    processor = info.context.processors.deployment
    _ = await processor.delete_auto_scaling_rule.wait_for_complete(
        DeleteAutoScalingRuleAction(auto_scaling_rule_id=UUID(input.id))
    )
    return DeleteAutoScalingRulePayload(id=ID(input.id))
