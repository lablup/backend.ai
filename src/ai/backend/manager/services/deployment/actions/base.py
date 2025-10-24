from typing import override

from ai.backend.manager.actions.action import BaseAction


class DeploymentBaseAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "deployment"
