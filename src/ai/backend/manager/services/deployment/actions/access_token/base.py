from typing import override

from ai.backend.manager.actions.action import BaseAction


class DeploymentAccessTokenBaseAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "deployment_access_token"
