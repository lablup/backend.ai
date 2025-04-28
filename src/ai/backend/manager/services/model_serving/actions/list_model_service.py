import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction
from ai.backend.manager.services.model_serving.types import CompactServiceInfo


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
class ListModelServiceActionResult(BaseActionResult):
    data: list[CompactServiceInfo]

    @override
    def entity_id(self) -> Optional[str]:
        return None
