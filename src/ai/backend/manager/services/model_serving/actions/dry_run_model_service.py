from __future__ import annotations

import dataclasses
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from pydantic import AnyUrl

from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
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
    tag: str | None
    startup_command: str | None
    bootstrap_script: str | None
    callback_url: AnyUrl | None
    owner_access_key: str | None
    open_to_public: bool
    config: ServiceConfig

    request_user_id: uuid.UUID
    sudo_session_enabled: bool

    model_service_prepare_ctx: ModelServicePrepareCtx

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    def with_revision(self, revision: ModelRevisionSpec) -> DryRunModelServiceAction:
        """Return a new action with revision results applied."""
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
class DryRunModelServiceActionResult(BaseActionResult):
    task_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return None
