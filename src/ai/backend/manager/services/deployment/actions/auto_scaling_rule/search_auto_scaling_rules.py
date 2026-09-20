from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.deployment.types import ModelDeploymentAutoScalingRuleData
from ai.backend.manager.models.endpoint.row import EndpointAutoScalingRuleRow


@dataclass(frozen=True)
class SearchAutoScalingRulesAction(
    GlobalSearcherOpsAction[EndpointAutoScalingRuleRow, ModelDeploymentAutoScalingRuleData]
):
    """Page through auto-scaling rules across every deployment."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_auto_scaling_rules"
