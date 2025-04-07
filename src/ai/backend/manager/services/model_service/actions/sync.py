from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import ModelServiceAction


class SyncAction(ModelServiceAction):
    def entity_id(self) -> Optional[str]:
        return None

    def operation_type(self) -> str:
        return "sync_model_service"


class SyncActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None
