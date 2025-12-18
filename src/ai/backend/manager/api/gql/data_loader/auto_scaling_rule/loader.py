from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.deployment.types import ModelDeploymentAutoScalingRuleData
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.batch_load_auto_scaling_rules import (
    BatchLoadAutoScalingRulesAction,
)
from ai.backend.manager.services.deployment.processors import DeploymentProcessors


async def load_auto_scaling_rules_by_ids(
    processor: DeploymentProcessors,
    auto_scaling_rule_ids: Sequence[uuid.UUID],
) -> list[Optional[ModelDeploymentAutoScalingRuleData]]:
    """Batch load auto scaling rules by their IDs.

    Args:
        processor: The deployment processor.
        auto_scaling_rule_ids: Sequence of auto scaling rule UUIDs to load.

    Returns:
        List of ModelDeploymentAutoScalingRuleData (or None if not found)
        in the same order as auto_scaling_rule_ids.
    """
    if not auto_scaling_rule_ids:
        return []

    action_result = await processor.batch_load_auto_scaling_rules.wait_for_complete(
        BatchLoadAutoScalingRulesAction(auto_scaling_rule_ids=list(auto_scaling_rule_ids))
    )

    rule_map = {rule.id: rule for rule in action_result.data}
    return [rule_map.get(rule_id) for rule_id in auto_scaling_rule_ids]
