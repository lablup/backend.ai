import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import ModelServiceAction
from ai.backend.manager.services.model_service.types import RequesterCtx, ServiceInfo


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
class GetModelServiceInfoActionResult(BaseActionResult):
    data: ServiceInfo

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.endpoint_id)
