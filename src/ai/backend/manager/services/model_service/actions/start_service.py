import uuid
from dataclasses import dataclass
from typing import Optional, override

from pydantic import AnyUrl

from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import ModelServiceAction
from ai.backend.manager.services.model_service.types import ServiceConfig, ValidationResult


@dataclass
class StartModelServiceAction(ModelServiceAction):
    owner_id: uuid.UUID

    service_name: str
    replicas: int
    image: str
    runtime_variant: RuntimeVariant
    architecture: str
    group: str
    domain: str
    cluster_size: int
    cluster_mode: ClusterMode
    tag: Optional[str]
    startup_command: Optional[str]
    bootstrap_script: Optional[str]
    callback_url: Optional[AnyUrl]
    owner_access_key: Optional[str]
    open_to_public: bool
    config: ServiceConfig

    sudo_session_enabled: bool

    validation_result: ValidationResult

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "start"


@dataclass
class StartModelServiceActionResult(BaseActionResult):
    task_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.task_id)
