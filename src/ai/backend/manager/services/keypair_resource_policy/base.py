from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class KeypairResourcePolicyAction(BaseAction):
    @override
    def entity_type(self):
        return "keypair_resource_policy"


@dataclass
class KeypairResourcePolicyBatchAction(BaseBatchAction):
    @override
    def entity_type(self):
        return "keypair_resource_policy"
