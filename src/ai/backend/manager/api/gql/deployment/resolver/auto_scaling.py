"""Auto-scaling rule resolver functions."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.common.api_handlers import Sentinel
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
from ai.backend.manager.data.deployment.scale import ModelDeploymentAutoScalingRuleCreator
from ai.backend.manager.data.deployment.scale_modifier import ModelDeploymentAutoScalingRuleModifier
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.create_auto_scaling_rule import (
    CreateAutoScalingRuleAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.delete_auto_scaling_rule import (
    DeleteAutoScalingRuleAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.update_auto_scaling_rule import (
    UpdateAutoScalingRuleAction,
)
from ai.backend.manager.types import OptionalState

# Mutation resolvers


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def create_auto_scaling_rule(
    input: CreateAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> CreateAutoScalingRulePayload:
    """Create a new auto-scaling rule for a deployment."""
    processor = info.context.processors.deployment
    dto = input.to_pydantic()
    result = await processor.create_auto_scaling_rule.wait_for_complete(
        action=CreateAutoScalingRuleAction(
            ModelDeploymentAutoScalingRuleCreator(
                model_deployment_id=dto.model_deployment_id,
                metric_source=dto.metric_source,
                metric_name=dto.metric_name,
                min_threshold=dto.min_threshold,
                max_threshold=dto.max_threshold,
                step_size=dto.step_size,
                time_window=dto.time_window,
                min_replicas=dto.min_replicas,
                max_replicas=dto.max_replicas,
            )
        )
    )
    return CreateAutoScalingRulePayload(
        auto_scaling_rule=AutoScalingRule.from_dataclass(result.data)
    )


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def update_auto_scaling_rule(
    input: UpdateAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> UpdateAutoScalingRulePayload:
    """Update an existing auto-scaling rule."""
    processor = info.context.processors.deployment
    dto = input.to_pydantic()
    metric_source_state = (
        OptionalState.nop()
        if dto.metric_source is None
        else OptionalState.update(dto.metric_source)
    )
    action_result = await processor.update_auto_scaling_rule.wait_for_complete(
        UpdateAutoScalingRuleAction(
            auto_scaling_rule_id=UUID(input.id),
            modifier=ModelDeploymentAutoScalingRuleModifier(
                metric_source=metric_source_state,
                metric_name=OptionalState.from_graphql(dto.metric_name),
                min_threshold=(
                    OptionalState.nop()
                    if isinstance(dto.min_threshold, Sentinel) or dto.min_threshold is None
                    else OptionalState.update(dto.min_threshold)
                ),
                max_threshold=(
                    OptionalState.nop()
                    if isinstance(dto.max_threshold, Sentinel) or dto.max_threshold is None
                    else OptionalState.update(dto.max_threshold)
                ),
                step_size=OptionalState.from_graphql(dto.step_size),
                time_window=OptionalState.from_graphql(dto.time_window),
                min_replicas=(
                    OptionalState.nop()
                    if isinstance(dto.min_replicas, Sentinel) or dto.min_replicas is None
                    else OptionalState.update(dto.min_replicas)
                ),
                max_replicas=(
                    OptionalState.nop()
                    if isinstance(dto.max_replicas, Sentinel) or dto.max_replicas is None
                    else OptionalState.update(dto.max_replicas)
                ),
            ),
        )
    )
    return UpdateAutoScalingRulePayload(
        auto_scaling_rule=AutoScalingRule.from_dataclass(action_result.data)
    )


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def delete_auto_scaling_rule(
    input: DeleteAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> DeleteAutoScalingRulePayload:
    """Delete an auto-scaling rule."""
    processor = info.context.processors.deployment
    pydantic_input = input.to_pydantic()
    _ = await processor.delete_auto_scaling_rule.wait_for_complete(
        DeleteAutoScalingRuleAction(auto_scaling_rule_id=pydantic_input.id)
    )
    return DeleteAutoScalingRulePayload(id=ID(str(pydantic_input.id)))
