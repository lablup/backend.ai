import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.auth.actions.base import (
    KeypairSingleEntityAction,
    KeypairSingleEntityActionResult,
)


@dataclass
class GetSSHKeypairAction(KeypairSingleEntityAction):
    user_id: uuid.UUID
    access_key: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.READ

    @override
    def target_entity_id(self) -> str:
        return self.access_key

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.KEYPAIR, self.access_key)


@dataclass
class GetSSHKeypairActionResult(KeypairSingleEntityActionResult):
    public_key: str
    access_key: str

    @override
    def target_entity_id(self) -> str:
        return self.access_key
