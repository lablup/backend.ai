"""Write specs for an auto-scaling rule of a deployment."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.auto_scaling_rule import AutoScalingRuleID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.types import AutoScalingMetricSource
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    ModelDeploymentAutoScalingRuleData,
)
from ai.backend.manager.models.endpoint.row import EndpointAutoScalingRuleRow
from ai.backend.manager.models.endpoint.searchable_fields import AutoScalingRuleSearchableFields
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from bai_scenario.seeds.seeder import TestSeedFieldCreator


@dataclass
class _AutoScalingRuleCreator(
    FieldCreator[DeploymentID, EndpointAutoScalingRuleRow, ModelDeploymentAutoScalingRuleData]
):
    """The manager inserts a rule through its repository, not a write spec."""

    metric_name: str
    step_size: int
    time_window: int

    @override
    def field_id(self, row: EndpointAutoScalingRuleRow) -> AutoScalingRuleID:
        return row.id

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: DeploymentID) -> EndpointAutoScalingRuleRow:
        return EndpointAutoScalingRuleRow(
            endpoint=owner_id,
            metric_source=AutoScalingMetricSource.KERNEL,
            metric_name=self.metric_name,
            min_threshold=None,
            max_threshold=None,
            step_size=self.step_size,
            cooldown_seconds=self.time_window,
            min_replicas=None,
            max_replicas=None,
            prometheus_query_preset_id=None,
        )

    @override
    def to_data(self, row: EndpointAutoScalingRuleRow) -> ModelDeploymentAutoScalingRuleData:
        return AutoScalingRuleSearchableFields.own.to_data(row)


@dataclass(frozen=True)
class TestSeedAutoScalingRuleOf(
    TestSeedFieldCreator[DeploymentInfo, ModelDeploymentAutoScalingRuleData]
):
    """A rule scaling the deployment by a kernel metric, with no thresholds or bounds."""

    metric_name: str = "cpu_util"
    step_size: int = 1
    time_window: int = 60

    @override
    def kind(self) -> str:
        return "자동 스케일링 규칙 하나를 갖는다"

    @override
    def owner_id(self, owner: DeploymentInfo) -> DeploymentID:
        return DeploymentID(owner.id)

    @override
    def seed(self) -> _AutoScalingRuleCreator:
        return _AutoScalingRuleCreator(
            metric_name=self.metric_name,
            step_size=self.step_size,
            time_window=self.time_window,
        )
