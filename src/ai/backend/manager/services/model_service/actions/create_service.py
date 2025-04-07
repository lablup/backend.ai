import uuid
from dataclasses import dataclass
from typing import Optional, override

from pydantic import AnyUrl

from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import ModelServiceAction
from ai.backend.manager.services.model_service.types import (
    ServiceConfig,
    ServiceInfo,
    ValidationResult,
)


@dataclass
class CreateModelServiceAction(ModelServiceAction):
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

    created_user_id: uuid.UUID

    sudo_session_enabled: bool

    validation_result: ValidationResult

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "create_model_service"


@dataclass
class CreateModelServiceActionResult(BaseActionResult):
    data: ServiceInfo

    @override
    def entity_id(self) -> Optional[str]:
        return None
