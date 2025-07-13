import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional, Self, Sequence

import yarl

from ai.backend.common.types import ClusterMode, ResourceSlot, RuntimeVariant, VFolderMount
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow, EndpointTokenRow
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.user import UserRow


@dataclass
class EndpointData:
    id: uuid.UUID
    name: str
    image: Optional[ImageData]
    domain: str
    project: uuid.UUID
    resource_group: str
    resource_slots: ResourceSlot
    url: str
    model: uuid.UUID
    model_definition_path: Optional[str]
    model_mount_destination: Optional[str]
    created_user_id: uuid.UUID
    created_user_email: Optional[str]
    session_owner_id: uuid.UUID
    session_owner_email: str
    tag: Optional[str]
    startup_command: Optional[str]
    bootstrap_script: Optional[str]
    callback_url: Optional[yarl.URL]
    environ: Optional[Mapping[str, Any]]
    resource_opts: Optional[Mapping[str, Any]]
    replicas: int
    cluster_mode: ClusterMode
    cluster_size: int
    open_to_public: bool
    created_at: datetime
    destroyed_at: Optional[datetime]
    retries: int
    lifecycle_stage: EndpointLifecycle
    runtime_variant: RuntimeVariant
    extra_mounts: Sequence[VFolderMount]
    routings: Optional[Sequence["RoutingData"]] = None

    @classmethod
    def from_row(cls, row: EndpointRow) -> Self:
        return cls(
            id=row.id,
            name=row.name,
            image=row.image_row.to_dataclass() if row.image_row else None,
            domain=row.domain,
            project=row.project,
            resource_group=row.resource_group,
            resource_slots=row.resource_slots,
            url=row.url,
            model=row.model,
            model_definition_path=row.model_definition_path,
            model_mount_destination=row.model_mount_destination,
            created_user_id=row.created_user,
            created_user_email=row.created_user_row.email
            if row.created_user_row is not None
            else None,
            session_owner_id=row.session_owner,
            session_owner_email=row.session_owner_row.email if row.session_owner_row else "",
            tag=row.tag,
            startup_command=row.startup_command,
            bootstrap_script=row.bootstrap_script,
            callback_url=row.callback_url,
            environ=row.environ,
            resource_opts=row.resource_opts,
            replicas=row.replicas,
            cluster_mode=ClusterMode(row.cluster_mode),
            cluster_size=row.cluster_size,
            open_to_public=row.open_to_public,
            created_at=row.created_at,
            destroyed_at=row.destroyed_at,
            retries=row.retries,
            lifecycle_stage=row.lifecycle_stage,
            runtime_variant=row.runtime_variant,
            extra_mounts=row.extra_mounts,
            routings=[RoutingData.from_row(routing) for routing in row.routings]
            if row.routings else None,
        )


@dataclass
class RoutingData:
    id: uuid.UUID
    endpoint: uuid.UUID
    session: Optional[uuid.UUID]
    status: RouteStatus
    traffic_ratio: float
    created_at: datetime
    error_data: dict[str, Any]

    @classmethod
    def from_row(cls, row: RoutingRow) -> Self:
        return cls(
            id=row.id,
            endpoint=row.endpoint,
            session=row.session,
            status=row.status,
            traffic_ratio=row.traffic_ratio,
            created_at=row.created_at,
            error_data=row.error_data,
        )


@dataclass
class EndpointTokenData:
    id: uuid.UUID
    token: str
    endpoint: uuid.UUID
    session_owner: uuid.UUID
    domain: str
    project: uuid.UUID
    created_at: datetime

    @classmethod
    def from_row(cls, row: EndpointTokenRow) -> Self:
        return cls(
            id=row.id,
            token=row.token,
            endpoint=row.endpoint,
            session_owner=row.session_owner,
            domain=row.domain,
            project=row.project,
            created_at=row.created_at,
        )


@dataclass
class UserData:
    uuid: uuid.UUID
    email: str

    @classmethod
    def from_row(cls, row: UserRow) -> Self:
        return cls(
            uuid=row.uuid,
            email=row.email,
        )


@dataclass
class ScalingGroupData:
    wsproxy_addr: str
    wsproxy_api_token: str