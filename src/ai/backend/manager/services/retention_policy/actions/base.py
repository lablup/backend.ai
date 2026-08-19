from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.global_action import BaseGlobalAction


@dataclass
class RetentionPolicyAction(BaseGlobalAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.RETENTION_POLICY
