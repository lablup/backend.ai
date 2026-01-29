from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, override

from pydantic import AnyUrl

from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.types import ModelServicePrepareCtx, ServiceConfig
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction

if TYPE_CHECKING:
    from ai.backend.manager.data.deployment.types import ModelRevisionSpec


@dataclass
class DryRunModelServiceAction(ModelServiceAction):
    service_name: str
    replicas: int
    image: str | None
    runtime_variant: RuntimeVariant
    architecture: str | None
    group_name: str
    domain_name: str
    cluster_size: int
    cluster_mode: ClusterMode
    tag: Optional[str]
    startup_command: Optional[str]
    bootstrap_script: Optional[str]
    callback_url: Optional[AnyUrl]
    owner_access_key: Optional[str]
    open_to_public: bool
    config: ServiceConfig

    request_user_id: uuid.UUID
    sudo_session_enabled: bool

    model_service_prepare_ctx: ModelServicePrepareCtx

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "start"

    def apply_revision(self, revision: ModelRevisionSpec) -> None:
        """Apply revision results to this action."""
        self.image = revision.image_identifier.canonical
        self.architecture = revision.image_identifier.architecture
        self.config.resources = dict(revision.resource_spec.resource_slots)
        if revision.execution.environ:
            self.config.environ = revision.execution.environ


@dataclass
class DryRunModelServiceActionResult(BaseActionResult):
    task_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None
