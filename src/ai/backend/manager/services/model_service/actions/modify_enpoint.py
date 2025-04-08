import uuid
from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.common.types import ClusterMode
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import EndpointAction
from ai.backend.manager.services.model_service.types import EndpointData, RequesterCtx
from ai.backend.manager.types import OptionalState


@dataclass
class ImageRef:
    name: str
    registry: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("registry"))
    architecture: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("architecture")
    )


@dataclass
class ExtraMount:
    vfolder_id: OptionalState[uuid.UUID] = field(
        default_factory=lambda: OptionalState.nop("vfolder_id")
    )
    mount_destination: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("mount_destination")
    )
    type: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("type"))
    permission: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("permission"))


@dataclass
class ModifyEndpointAction(EndpointAction):
    requester_ctx: RequesterCtx
    endpoint_id: uuid.UUID
    resource_slots: OptionalState[dict[str, Any]] = field(
        default_factory=lambda: OptionalState.nop("resource_slots")
    )
    resource_opts: OptionalState[dict[str, Any]] = field(
        default_factory=lambda: OptionalState.nop("resource_opts")
    )
    cluster_mode: OptionalState[ClusterMode] = field(
        default_factory=lambda: OptionalState.nop("cluster_mode")
    )
    cluster_size: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("cluster_size")
    )
    replicas: OptionalState[int] = field(default_factory=lambda: OptionalState.nop("replicas"))
    desired_session_count: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("desired_session_count")
    )
    image: OptionalState[ImageRef] = field(default_factory=lambda: OptionalState.nop("image"))
    name: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("name"))
    resource_group: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("resource_group")
    )
    model_definition_path: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("model_definition_path")
    )
    open_to_public: OptionalState[bool] = field(
        default_factory=lambda: OptionalState.nop("open_to_public")
    )
    extra_mounts: OptionalState[list[ExtraMount]] = field(
        default_factory=lambda: OptionalState.nop("extra_mounts")
    )
    environ: OptionalState[dict[str, str]] = field(
        default_factory=lambda: OptionalState.nop("environ")
    )
    runtime_variant: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("runtime_variant")
    )

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "modify_endpoint"


@dataclass
class ModifyEndpointActionResult(BaseActionResult):
    success: bool
    data: Optional[EndpointData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
