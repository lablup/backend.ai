"""Data containers for model serving operations.

Note: These are data containers, not CreatorSpec implementations.
For row creation, use EndpointCreatorSpec from repositories/model_serving/creators.py
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import AnyUrl

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    RuntimeVariant,
)
from ai.backend.manager.data.model_serving.types import (
    ModelServicePrepareCtx,
    ServiceConfig,
)

if TYPE_CHECKING:
    from ai.backend.manager.data.deployment.types import ModelRevisionSpec


@dataclass
class ModelServiceCreator:
    """Data container for model service creation parameters.

    This is not a CreatorSpec - it's used to collect and pass service creation
    parameters in the service layer before creating an EndpointCreatorSpec.
    """

    service_name: str
    replicas: int
    image: str | None
    runtime_variant: RuntimeVariant
    architecture: str | None
    group_name: str
    domain_name: str
    cluster_size: int
    cluster_mode: ClusterMode
    open_to_public: bool
    config: ServiceConfig
    sudo_session_enabled: bool
    model_service_prepare_ctx: ModelServicePrepareCtx
    tag: str | None = None
    startup_command: str | None = None
    bootstrap_script: str | None = None
    callback_url: AnyUrl | None = None

    def with_revision(self, revision: ModelRevisionSpec) -> ModelServiceCreator:
        """Return a new creator with revision results applied."""
        overrided_service_config = dataclasses.replace(
            self.config,
            resources=dict(revision.resource_spec.resource_slots),
            environ=revision.execution.environ,
        )
        return dataclasses.replace(
            self,
            image=revision.image_identifier.canonical,
            architecture=revision.image_identifier.architecture,
            config=overrided_service_config,
        )


@dataclass
class EndpointAutoScalingRuleCreator:
    """Data container for endpoint auto scaling rule creation parameters.

    This is not a CreatorSpec - the repository extracts individual fields
    and creates the row directly without using CreatorSpec pattern.
    """

    metric_source: AutoScalingMetricSource
    metric_name: str
    threshold: str
    comparator: AutoScalingMetricComparator
    step_size: int
    cooldown_seconds: int
    min_replicas: int | None = None
    max_replicas: int | None = None
