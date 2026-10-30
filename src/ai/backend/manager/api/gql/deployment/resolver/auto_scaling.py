"""Auto-scaling rule resolver functions."""

from __future__ import annotations

from uuid import UUID

from strawberry import ID, Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.deployment.types.auto_scaling import (
    AutoScalingRule,
    CreateAutoScalingRuleInput,
    CreateAutoScalingRulePayload,
    DeleteAutoScalingRuleInput,
    DeleteAutoScalingRulePayload,
    PartialBulkAutoScalingRulesPayload,
    PartialBulkPurgeAutoScalingRulesInput,
    PartialBulkUpdateAutoScalingRulesInput,
    PurgeAutoScalingRulePayload,
    UpdateAutoScalingRuleInput,
    UpdateAutoScalingRulePayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

# Mutation resolvers


@gql_mutation(BackendAIGQLMeta(added_version="25.16.0", description="Create auto scaling rule."))
async def create_auto_scaling_rule(
    input: CreateAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> CreateAutoScalingRulePayload | None:
    """Create a new auto-scaling rule for a deployment."""
    payload = await info.context.adapters.deployment.create_rule(input.to_pydantic())
    return CreateAutoScalingRulePayload(rule=AutoScalingRule.from_pydantic(payload.rule))


@gql_mutation(BackendAIGQLMeta(added_version="25.16.0", description="Update auto scaling rule."))
async def update_auto_scaling_rule(
    input: UpdateAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> UpdateAutoScalingRulePayload | None:
    """Update an existing auto-scaling rule."""
    payload = await info.context.adapters.deployment.update_rule(input.to_pydantic())
    return UpdateAutoScalingRulePayload(rule=AutoScalingRule.from_pydantic(payload.rule))


@gql_mutation(
    BackendAIGQLMeta(added_version="25.16.0", description="Delete auto scaling rule."),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgeAutoScalingRule`.",
)
async def delete_auto_scaling_rule(
    input: DeleteAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> DeleteAutoScalingRulePayload | None:
    """Delete an auto-scaling rule."""
    payload = await info.context.adapters.deployment.purge_rule(input.to_pydantic().id)
    return DeleteAutoScalingRulePayload(id=ID(str(payload.id)))


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Permanently remove an auto-scaling rule."
    )
)
async def purge_auto_scaling_rule(
    id: UUID, info: Info[StrawberryGQLContext]
) -> PurgeAutoScalingRulePayload:
    payload = await info.context.adapters.deployment.purge_rule(id)
    return PurgeAutoScalingRulePayload.from_pydantic(
        payload, extra={"purged_id": to_global_id(AutoScalingRule, payload.field_id)}
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several auto-scaling rules, answering for each one.",
    )
)
async def partial_bulk_update_auto_scaling_rules(
    input: PartialBulkUpdateAutoScalingRulesInput, info: Info[StrawberryGQLContext]
) -> PartialBulkAutoScalingRulesPayload:
    payload = await info.context.adapters.deployment.partial_bulk_update_rules(input.to_pydantic())
    return PartialBulkAutoScalingRulesPayload.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove several auto-scaling rules, answering for each one.",
    )
)
async def partial_bulk_purge_auto_scaling_rules(
    input: PartialBulkPurgeAutoScalingRulesInput, info: Info[StrawberryGQLContext]
) -> PartialBulkAutoScalingRulesPayload:
    payload = await info.context.adapters.deployment.partial_bulk_purge_rules(input.to_pydantic())
    return PartialBulkAutoScalingRulesPayload.from_pydantic(payload)
