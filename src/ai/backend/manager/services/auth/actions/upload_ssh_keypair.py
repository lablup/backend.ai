import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.auth.types import SSHKeypair
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.auth.actions.base import (
    KeypairScopeAction,
    KeypairScopeActionResult,
)


@dataclass
class UploadSSHKeypairAction(KeypairScopeAction):
    user_id: uuid.UUID
    public_key: str
    private_key: str
    access_key: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, str(self.user_id))


@dataclass
class UploadSSHKeypairActionResult(KeypairScopeActionResult):
    ssh_keypair: SSHKeypair
    user_id: uuid.UUID

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.user_id)
