from typing import override

from ai.backend.manager.actions.action.base import BaseAction


class UserAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "user"
