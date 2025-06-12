from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class UserResourcePolicyAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "user_resource_policy"


@dataclass
class UserResourcePolicyBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "user_resource_policy"
