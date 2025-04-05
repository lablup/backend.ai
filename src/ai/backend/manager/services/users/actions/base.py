from typing import override

from ai.backend.manager.actions.action import BaseAction


class UserAction(BaseAction):
    @override
    def entity_type(self) -> str:
        return "user"
