from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import ModelServiceAction


class UpdateRouteAction(ModelServiceAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "update_route"


class UpdateRouteActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None
