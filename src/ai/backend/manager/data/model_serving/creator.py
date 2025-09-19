import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional, override

import yarl
from pydantic import AnyUrl

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.manager.data.model_serving.types import (
    EndpointLifecycle,
    ModelServicePrepareCtx,
    ServiceConfig,
)
from ai.backend.manager.types import Creator


@dataclass
class EndpointCreator(Creator):
    name: str
    model_definition_path: Optional[str]
    created_user: uuid.UUID
    session_owner: uuid.UUID
    image: uuid.UUID  # Image row ID
    model: uuid.UUID  # vfolder row ID
    domain: str
    project: uuid.UUID
    resource_group: str  # Resource group row ID which is the name
    resource_slots: Mapping[str, Any]
    replicas: int = 0
    lifecycle_stage: EndpointLifecycle = EndpointLifecycle.CREATED
    tag: Optional[str] = None
    startup_command: Optional[str] = None
    bootstrap_script: Optional[str] = None
    callback_url: Optional[yarl.URL] = None
    environ: Optional[dict[str, str]] = None
    open_to_public: bool = False
    runtime_variant: RuntimeVariant = RuntimeVariant.CUSTOM
    model_mount_destination: str = "/models"
    url: Optional[str] = None
    resource_opts: Optional[dict[str, Any]] = None
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE
    cluster_size: int = 1
    extra_mounts: list[VFolderMount] = field(default_factory=list)
    retries: int = 0

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "model_definition_path": self.model_definition_path,
            "created_user": self.created_user,
            "session_owner": self.session_owner,
            "image": self.image,
            "model": self.model,
            "domain": self.domain,
            "project": self.project,
            "resource_group": self.resource_group,
            "resource_slots": self.resource_slots,
            "replicas": self.replicas,
            "lifecycle_stage": self.lifecycle_stage,
            "tag": self.tag,
            "startup_command": self.startup_command,
            "bootstrap_script": self.bootstrap_script,
            "callback_url": self.callback_url,
            "environ": self.environ,
            "open_to_public": self.open_to_public,
            "runtime_variant": self.runtime_variant,
            "model_mount_destination": self.model_mount_destination,
            "url": self.url,
            "resource_opts": self.resource_opts,
            "cluster_mode": self.cluster_mode,
            "cluster_size": self.cluster_size,
            "extra_mounts": self.extra_mounts,
        }


@dataclass
class ModelServiceCreator(Creator):
    service_name: str
    replicas: int
    image: str
    runtime_variant: RuntimeVariant
    architecture: str
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

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {}


@dataclass
class EndpointAutoScalingRuleCreator(Creator):
    metric_source: AutoScalingMetricSource
    metric_name: str
    threshold: str
    comparator: AutoScalingMetricComparator
    step_size: int
    cooldown_seconds: int
    min_replicas: Optional[int] = None
    max_replicas: Optional[int] = None

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "metric_source": self.metric_source,
            "metric_name": self.metric_name,
            "threshold": self.threshold,
            "comparator": self.comparator,
            "step_size": self.step_size,
            "cooldown_seconds": self.cooldown_seconds,
            "min_replicas": self.min_replicas,
            "max_replicas": self.max_replicas,
        }
