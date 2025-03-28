from typing import override

from ai.backend.manager.actions.action import BaseAction


class GroupAction(BaseAction):
    @override
    def entity_type(self) -> str:
        return "group"
