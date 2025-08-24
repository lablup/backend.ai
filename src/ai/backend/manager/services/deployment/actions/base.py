from typing import override

from ai.backend.manager.actions.action import BaseAction


class DeploymentAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "deployment"


class AutoscaleAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "autoscale"
