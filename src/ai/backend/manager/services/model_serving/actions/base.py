from typing import override

from ai.backend.manager.actions.action.base import BaseAction


class ModelServiceAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "model_service"
