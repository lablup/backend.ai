from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.global_action import BaseGlobalAction


class IdleCheckerGlobalAction(BaseGlobalAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.IDLE_CHECKER
