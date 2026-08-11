from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfs_storage import VFS_STORAGE_ENTITY_TYPE
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class GetQuotaScopeAction(BaseGlobalAction):
    storage_host_name: str
    quota_scope_id: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFS_STORAGE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_vfs_quota_scope"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetQuotaScopeActionResult(BaseActionResult):
    quota_scope_id: str
    storage_host_name: str
    usage_bytes: int | None
    usage_count: int | None
    hard_limit_bytes: int | None

    @override
    def entity_id(self) -> str | None:
        return self.quota_scope_id
