"""Endpoint and route data types for deployment repository."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Self

from ai.backend.common.types import SessionId
from ai.backend.manager.data.model_serving.creator import ModelServiceCreator
from ai.backend.manager.data.model_serving.types import EndpointLifecycle, RouteStatus


@dataclass
class EndpointCreationArgs:
    """Arguments for creating an endpoint."""

    name: str
    model_id: uuid.UUID
    owner_id: uuid.UUID
    group_id: uuid.UUID
    domain_name: str
    is_public: bool
    runtime_variant: str
    desired_session_count: int
    resource_opts: dict[str, Any]
    scaling_group: Optional[str] = None

    @classmethod
    def _parse_resource_opts_from_creator(cls, creator: ModelServiceCreator) -> dict[str, Any]:
        return {
            "image_ref": creator.image,
            "architecture": creator.architecture,
            "access_key": creator.model_service_prepare_ctx.owner_access_key,
            "scaling_group": creator.config.scaling_group,
            "cluster_size": creator.cluster_size,
            "cluster_mode": creator.cluster_mode,
            "resources": creator.config.resources,
            "resource_opts": creator.config.resource_opts,
            "environ": creator.config.environ or {},
            "model_mount_destination": creator.config.model_mount_destination,
            "extra_mounts": [
                {
                    "vfolder_id": str(vfolder_id),
                    "mount_path": mount_option.mount_destination or f"/mnt/{vfolder_id}",
                    "permission": mount_option.permission.value
                    if mount_option.permission
                    else "rw",
                }
                for vfolder_id, mount_option in creator.config.extra_mounts.items()
            ],
            "sudo_session_enabled": creator.sudo_session_enabled,
            "bootstrap_script": creator.bootstrap_script,
            "startup_command": creator.startup_command or creator.config.model_definition_path,
            "callback_url": creator.callback_url,
            "tag": creator.tag,
        }

    @classmethod
    def from_creator(cls, creator: ModelServiceCreator) -> Self:
        return cls(
            name=creator.service_name,
            model_id=creator.model_service_prepare_ctx.model_id,
            owner_id=creator.model_service_prepare_ctx.owner_uuid,
            group_id=creator.model_service_prepare_ctx.group_id,
            domain_name=creator.domain_name,
            is_public=creator.open_to_public,
            runtime_variant=creator.runtime_variant,
            desired_session_count=creator.replicas,
            resource_opts=cls._parse_resource_opts_from_creator(creator),
            scaling_group=creator.config.scaling_group,
        )


@dataclass
class EndpointData:
    """Data structure for model service endpoint."""

    endpoint_id: uuid.UUID
    name: str
    model_id: uuid.UUID
    owner_id: uuid.UUID
    group_id: uuid.UUID
    domain_name: str
    lifecycle: EndpointLifecycle
    is_public: bool
    runtime_variant: str
    desired_session_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    service_endpoint: Optional[str] = None
    resource_opts: dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteData:
    """Data structure for model service route."""

    route_id: uuid.UUID
    endpoint_id: uuid.UUID
    session_id: Optional[SessionId]
    status: RouteStatus
    traffic_ratio: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class EndpointWithRoutesData:
    """Data structure containing endpoint with its routes."""

    endpoint: EndpointData
    routes: list[RouteData]
