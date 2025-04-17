import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, override

from dateutil.relativedelta import relativedelta
from pydantic import AnyUrl

from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.services.model_service.types import (
    CompactServiceInfo,
    EndpointData,
    EndpointModifier,
    ErrorInfo,
    ModelServiceCreator,
    ModelServicePrepareCtx,
    RequesterCtx,
    ServiceConfig,
    ServiceInfo,
)


class ModelServiceAction(BaseAction):
    @override
    def entity_type(self) -> str:
        return "model_service"


@dataclass
class CreateModelServiceAction(ModelServiceAction):
    request_user_id: uuid.UUID
    creator: ModelServiceCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "create"


@dataclass
class StartModelServiceAction(ModelServiceAction):
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
    def operation_type(self) -> str:
        return "start"


@dataclass
class ListModelServiceAction(ModelServiceAction):
    session_owener_id: uuid.UUID
    name: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "list"


@dataclass
class DeleteModelServiceAction(ModelServiceAction):
    service_id: uuid.UUID
    requester_ctx: RequesterCtx

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "delete"


@dataclass
class ModifyEndpointAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    endpoint_id: uuid.UUID
    modifier: EndpointModifier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "modify"


@dataclass
class GetModelServiceInfoAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    service_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "get"


@dataclass
class ListErrorsAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    service_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "list"


@dataclass
class ClearErrorAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    service_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "clear"


@dataclass
class UpdateRouteAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    service_id: uuid.UUID
    route_id: uuid.UUID
    traffic_ratio: float

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "update"


@dataclass
class DeleteRouteAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    service_id: uuid.UUID
    route_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "delete"


@dataclass
class GenerateTokenAction(ModelServiceAction):
    requester_ctx: RequesterCtx

    service_id: uuid.UUID

    duration: Optional[timedelta | relativedelta]
    valid_until: Optional[int]
    expires_at: int

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "generate"


@dataclass
class ForceSyncAction(ModelServiceAction):
    service_id: uuid.UUID
    requester_ctx: RequesterCtx

    def entity_id(self) -> Optional[str]:
        return None

    def operation_type(self) -> str:
        return "sync"


@dataclass
class CreateModelServiceActionResult(BaseActionResult):
    data: ServiceInfo

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.endpoint_id)


@dataclass
class StartModelServiceActionResult(BaseActionResult):
    task_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.task_id)


@dataclass
class ListModelServiceActionResult(BaseActionResult):
    data: list[CompactServiceInfo]

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class DeleteModelServiceActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class ModifyEndpointActionResult(BaseActionResult):
    success: bool
    data: Optional[EndpointData]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data is not None else None


@dataclass
class GetModelServiceInfoActionResult(BaseActionResult):
    data: ServiceInfo

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.endpoint_id)


@dataclass
class ListErrorsActionResult(BaseActionResult):
    error_info: list[ErrorInfo]
    retries: int

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class ClearErrorActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class UpdateRouteActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class DeleteRouteActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class GenerateTokenActionResult(BaseActionResult):
    token: str

    @override
    def entity_id(self) -> Optional[str]:
        return self.token


@dataclass
class ForceSyncActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
