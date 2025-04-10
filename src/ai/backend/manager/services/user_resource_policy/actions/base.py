from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class UserResourcePolicyAction(BaseAction):
    @override
    def entity_type(self):
        return "user_resource_policy"


@dataclass
class UserResourcePolicyBatchAction(BaseBatchAction):
    @override
    def entity_type(self):
        return "user_resource_policy"
