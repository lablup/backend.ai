"""Data containers for model serving operations.

Note: These are data containers, not CreatorSpec implementations.
For row creation, use EndpointCreatorSpec from repositories/model_serving/creators.py
"""

from dataclasses import dataclass
from typing import Optional

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


@dataclass
class ModelServiceCreator:
    """Data container for model service creation parameters.

    This is not a CreatorSpec - it's used to collect and pass service creation
    parameters in the service layer before creating an EndpointCreatorSpec.
    """

    service_name: str
    replicas: int
    image: Optional[str]
    runtime_variant: RuntimeVariant
    architecture: Optional[str]
    group_name: str
    domain_name: str
    cluster_size: int
    cluster_mode: ClusterMode
    open_to_public: bool
    config: ServiceConfig
    sudo_session_enabled: bool
    model_service_prepare_ctx: ModelServicePrepareCtx
    tag: Optional[str] = None
    startup_command: Optional[str] = None
    bootstrap_script: Optional[str] = None
    callback_url: Optional[AnyUrl] = None


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
    min_replicas: Optional[int] = None
    max_replicas: Optional[int] = None
