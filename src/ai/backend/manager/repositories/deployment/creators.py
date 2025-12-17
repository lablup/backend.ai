"""CreatorSpec implementations for deployment domain."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

from typing_extensions import override

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ResourceSlot,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class DeploymentRevisionCreatorSpec(CreatorSpec[DeploymentRevisionRow]):
    """CreatorSpec for deployment revision creation.

    Note: revision_number must be provided by the service layer after
    calculating from get_latest_revision_number().
    """

    endpoint: uuid.UUID
    revision_number: int
    image: uuid.UUID
    resource_group: str
    resource_slots: ResourceSlot
    resource_opts: Mapping[str, Any]
    cluster_mode: str
    cluster_size: int
    model: Optional[uuid.UUID]
    model_mount_destination: str
    model_definition_path: Optional[str]
    model_definition: Optional[Mapping[str, Any]]
    startup_command: Optional[str]
    bootstrap_script: Optional[str]
    environ: Mapping[str, Any]
    callback_url: Optional[str]
    runtime_variant: RuntimeVariant
    extra_mounts: Sequence[VFolderMount]

    @override
    def build_row(self) -> DeploymentRevisionRow:
        return DeploymentRevisionRow(
            endpoint=self.endpoint,
            revision_number=self.revision_number,
            image=self.image,
            model=self.model,
            model_mount_destination=self.model_mount_destination,
            model_definition_path=self.model_definition_path,
            model_definition=self.model_definition,
            resource_group=self.resource_group,
            resource_slots=self.resource_slots,
            resource_opts=self.resource_opts,
            cluster_mode=self.cluster_mode,
            cluster_size=self.cluster_size,
            startup_command=self.startup_command,
            bootstrap_script=self.bootstrap_script,
            environ=self.environ,
            callback_url=self.callback_url,
            runtime_variant=self.runtime_variant,
            extra_mounts=list(self.extra_mounts),
        )


@dataclass
class DeploymentAutoScalingPolicyCreatorSpec(CreatorSpec[DeploymentAutoScalingPolicyRow]):
    """CreatorSpec for deployment auto-scaling policy creation.

    Each endpoint can have at most one auto-scaling policy (1:1 relationship).
    The policy supports dual thresholds for hysteresis-based scaling.
    """

    endpoint: uuid.UUID
    min_replicas: int
    max_replicas: int
    metric_source: Optional[AutoScalingMetricSource]
    metric_name: Optional[str]
    comparator: Optional[AutoScalingMetricComparator]
    scale_up_threshold: Optional[Decimal]
    scale_down_threshold: Optional[Decimal]
    scale_up_step_size: int
    scale_down_step_size: int
    cooldown_seconds: int

    @override
    def build_row(self) -> DeploymentAutoScalingPolicyRow:
        return DeploymentAutoScalingPolicyRow(
            endpoint=self.endpoint,
            min_replicas=self.min_replicas,
            max_replicas=self.max_replicas,
            metric_source=self.metric_source,
            metric_name=self.metric_name,
            comparator=self.comparator,
            scale_up_threshold=self.scale_up_threshold,
            scale_down_threshold=self.scale_down_threshold,
            scale_up_step_size=self.scale_up_step_size,
            scale_down_step_size=self.scale_down_step_size,
            cooldown_seconds=self.cooldown_seconds,
        )
