"""CreatorSpec implementations for model serving domain."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

import yarl

from ai.backend.common.types import (
    ClusterMode,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.models.endpoint import EndpointRow, EndpointTokenRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class EndpointCreatorSpec(CreatorSpec[EndpointRow]):
    """CreatorSpec for endpoint creation."""

    name: str
    model_definition_path: str | None
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
    tag: str | None = None
    startup_command: str | None = None
    bootstrap_script: str | None = None
    callback_url: yarl.URL | None = None
    environ: dict[str, str] | None = None
    open_to_public: bool = False
    runtime_variant: RuntimeVariant = RuntimeVariant.CUSTOM
    model_mount_destination: str = "/models"
    url: str | None = None
    resource_opts: dict[str, Any] | None = None
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE
    cluster_size: int = 1
    extra_mounts: list[VFolderMount] = field(default_factory=list)
    retries: int = 0

    @override
    def build_row(self) -> EndpointRow:
        return EndpointRow(
            name=self.name,
            model_definition_path=self.model_definition_path,
            created_user=self.created_user,
            session_owner=self.session_owner,
            replicas=self.replicas,
            image=self.image,
            model=self.model,
            domain=self.domain,
            project=self.project,
            resource_group=self.resource_group,
            resource_slots=self.resource_slots,
            cluster_mode=self.cluster_mode,
            cluster_size=self.cluster_size,
            extra_mounts=self.extra_mounts,
            runtime_variant=self.runtime_variant,
            model_mount_destination=self.model_mount_destination,
            tag=self.tag,
            startup_command=self.startup_command,
            bootstrap_script=self.bootstrap_script,
            callback_url=self.callback_url,
            environ=self.environ,
            resource_opts=self.resource_opts,
            open_to_public=self.open_to_public,
        )


@dataclass
class EndpointTokenCreatorSpec(CreatorSpec[EndpointTokenRow]):
    """CreatorSpec for endpoint token creation."""

    id: uuid.UUID
    token: str
    endpoint: uuid.UUID
    domain: str
    project: uuid.UUID
    session_owner: uuid.UUID

    @override
    def build_row(self) -> EndpointTokenRow:
        return EndpointTokenRow(
            id=self.id,
            token=self.token,
            endpoint=self.endpoint,
            domain=self.domain,
            project=self.project,
            session_owner=self.session_owner,
        )
