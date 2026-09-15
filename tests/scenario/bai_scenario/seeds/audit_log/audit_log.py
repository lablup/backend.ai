"""Write spec for one audit record.

A record is laid the way the monitors write one: through the field creator, under the
entity it is about. No adapter call makes one, so a scenario that needs a record to read
lays it here. Its ``triggered_by`` is set from a user an earlier step laid, never a
literal, so the two stay in step.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override
from uuid import UUID, uuid4

from bai_scenario.seeds.seeder import SeedField, SeedFieldWithNestedRows

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.creators import (
    AuditLogScopeCreator,
    ScopeAuditLogCreator,
    SingleEntityAuditLogCreator,
)
from ai.backend.manager.models.specs.creator import NestedFieldCreator


@dataclass(frozen=True)
class SeedAuditRecord[Owner](SeedField[Owner, AuditLogData]):
    """One record of an operation on the entity ``owner_of`` reads off the laid row.

    The record's ``triggered_by`` is a user id, or none; the actor axis of a scoped read
    matches on it while the entity axis matches on the owner.
    """

    owner_of: Callable[[Owner], EntityIdentifier]
    operation: str
    created_at: datetime
    status: OperationStatus = OperationStatus.SUCCESS
    triggered_by: UserID | None = None

    @override
    def kind(self) -> str:
        parts = [f"'{self.operation}' 기록"]
        if self.status is not OperationStatus.SUCCESS:
            parts.append(f"{self.status.value} 상태")
        if self.triggered_by is not None:
            parts.append("실행한 사용자가 정해져 있음")
        return ", ".join(parts)

    @override
    def owner_id(self, owner: Owner) -> EntityIdentifier:
        return self.owner_of(owner)

    @override
    def seed(self) -> SingleEntityAuditLogCreator:
        return SingleEntityAuditLogCreator(
            action_id=uuid4(),
            operation=self.operation,
            action_name=self.operation,
            created_at=self.created_at,
            description=f"{self.operation} was recorded",
            status=self.status,
            request_id=None,
            triggered_by=str(self.triggered_by) if self.triggered_by is not None else None,
            acted_as=None,
            duration=None,
            client_ip=None,
        )


@dataclass(frozen=True)
class SeedScopedAuditRecord[Owner](SeedFieldWithNestedRows[Owner, AuditLogData]):
    """A scope-action record: written under the entity it affected, tagged with the scopes
    the run covered. A search by one of those scopes finds it through ``audit_log_scopes``,
    not through the record's own entity.
    """

    owner_of: Callable[[Owner], EntityIdentifier]
    operation: str
    created_at: datetime
    status: OperationStatus = OperationStatus.SUCCESS
    triggered_by: UserID | None = None
    scopes: tuple[tuple[EntityType, UUID], ...] = field(default_factory=tuple)

    @override
    def kind(self) -> str:
        return f"'{self.operation}' 기록, 스코프 {len(self.scopes)}개 달림"

    @override
    def owner_id(self, owner: Owner) -> EntityIdentifier:
        return self.owner_of(owner)

    @override
    def field(self) -> ScopeAuditLogCreator:
        return ScopeAuditLogCreator(
            action_id=uuid4(),
            operation=self.operation,
            action_name=self.operation,
            created_at=self.created_at,
            description=f"{self.operation} was recorded",
            status=self.status,
            request_id=None,
            triggered_by=str(self.triggered_by) if self.triggered_by is not None else None,
            acted_as=None,
            duration=None,
            client_ip=None,
        )

    @override
    def nested(self) -> Sequence[NestedFieldCreator[Any, Any, Any]]:
        return [
            AuditLogScopeCreator(scope_type=str(scope_type), scope_id=scope_id)
            for scope_type, scope_id in self.scopes
        ]
