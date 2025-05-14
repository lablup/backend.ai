from typing import override

from ai.backend.manager.actions.action import BaseAction


class GroupAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "group"
