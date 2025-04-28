from typing import override

from ai.backend.manager.actions.action import BaseAction


class ModelServiceAction(BaseAction):
    @override
    def entity_type(self) -> str:
        return "model_service"
