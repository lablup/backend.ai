from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import ModelServiceAction


class ScaleAction(ModelServiceAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    def operation_type(self) -> str:
        return "scale_model_service"


class ScaleActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None
