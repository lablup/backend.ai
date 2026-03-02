from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfs_storage.actions.base import VFSStorageAction


@dataclass
class QuotaScopeInfo:
    quota_scope_id: str
    storage_host_name: str
    usage_bytes: int | None
    usage_count: int | None
    hard_limit_bytes: int | None


@dataclass
class SearchQuotaScopesAction(VFSStorageAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchQuotaScopesActionResult(BaseActionResult):
    quota_scopes: list[QuotaScopeInfo]

    @override
    def entity_id(self) -> str | None:
        return None
