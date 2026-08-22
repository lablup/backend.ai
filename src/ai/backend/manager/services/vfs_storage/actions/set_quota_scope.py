from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfs_storage import VFS_STORAGE_ENTITY_TYPE
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class SetQuotaScopeAction(BaseGlobalAction):
    storage_host_name: str
    quota_scope_id: str
    hard_limit_bytes: int

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFS_STORAGE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "set_vfs_quota_scope"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class SetQuotaScopeActionResult:
    quota_scope_id: str
    storage_host_name: str
    usage_bytes: int | None
    usage_count: int | None
    hard_limit_bytes: int | None
