from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.audit_log.actions.base import AuditLogAction


@dataclass
class SearchAuditLogsAction(AuditLogAction):
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class SearchAuditLogsActionResult(BaseActionResult):
    data: list[AuditLogData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
