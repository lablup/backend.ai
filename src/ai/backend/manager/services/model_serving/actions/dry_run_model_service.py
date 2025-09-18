import uuid
from dataclasses import dataclass
from typing import Optional, override

from pydantic import AnyUrl

from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.types import ModelServicePrepareCtx, ServiceConfig
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class DryRunModelServiceAction(ModelServiceAction):
    service_name: str
    replicas: int
    image: str
    runtime_variant: RuntimeVariant
    architecture: str
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


@dataclass
class DryRunModelServiceActionResult(BaseActionResult):
    task_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None
