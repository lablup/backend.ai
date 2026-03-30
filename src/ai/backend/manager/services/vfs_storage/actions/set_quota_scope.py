from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfs_storage.actions.base import VFSStorageAction


@dataclass
class SetQuotaScopeAction(VFSStorageAction):
    storage_host_name: str
    quota_scope_id: str
    hard_limit_bytes: int

    @override
    def entity_id(self) -> str | None:
        return self.quota_scope_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class SetQuotaScopeActionResult(BaseActionResult):
    quota_scope_id: str
    storage_host_name: str
    usage_bytes: int | None
    usage_count: int | None
    hard_limit_bytes: int | None

    @override
    def entity_id(self) -> str | None:
        return self.quota_scope_id
