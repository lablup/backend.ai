from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class KeypairResourcePolicyAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "keypair_resource_policy"


@dataclass
class KeypairResourcePolicyBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "keypair_resource_policy"
