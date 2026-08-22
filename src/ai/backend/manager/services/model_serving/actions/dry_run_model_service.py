from __future__ import annotations

import dataclasses
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from pydantic import AnyUrl

from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import ModelServicePrepareCtx, ServiceConfig
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceScopeAction,
    ModelServiceScopeActionResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.data.deployment.types import ModelRevisionSpec


@dataclass
class DryRunModelServiceAction(ModelServiceScopeAction):
    project_id: ProjectID
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
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.project_id),)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    def with_revision(
        self,
        revision: ModelRevisionSpec,
        image: str,
        architecture: str,
    ) -> DryRunModelServiceAction:
        """Return a new action with revision results applied.

        Image canonical / architecture are resolved by the caller from the
        revision's ``image_id`` since the spec no longer carries them.
        """
        overrided_service_config = dataclasses.replace(
            self.config,
            resources=dict(revision.resource_spec.resource_slots),
            environ=revision.execution.environ,
        )
        return dataclasses.replace(
            self,
            image=image,
            architecture=architecture,
            config=overrided_service_config,
        )

    @override
    @classmethod
    def action_name(cls) -> str:
        return "dry_run_model_service"


@dataclass
class DryRunModelServiceActionResult(ModelServiceScopeActionResult):
    task_id: uuid.UUID
