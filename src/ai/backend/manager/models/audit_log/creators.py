"""Insert specs for audit rows, which ride beside the entity graph."""

from __future__ import annotations

import uuid
from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import override

from ai.backend.common.data.entity.action import ActionID
from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.types import EntityID, ScopeID
from ai.backend.manager.actions.types import ActionKind, OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogScopeData
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.specs.creator import SidecarCreator, SidecarFieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

__all__ = (
    "AuditLogCreator",
    "SingleEntityAuditLogCreator",
    "BulkAuditLogCreator",
    "ScopeAuditLogCreator",
    "LookupAuditLogCreator",
    "GlobalAuditLogCreator",
    "LegacyAuditLogCreator",
    "AuditLogScopeCreator",
)


@dataclass
class AuditLogCreator(SidecarCreator[AuditLogRow, AuditLogData]):
    """Fields every audit row is written with.

    Subclasses add the one target field their shape has and declare their
    ``action_kind``, so neither is something a writer can get wrong.
    """

    action_id: ActionID
    entity_type: str
    operation: str
    action_name: str
    created_at: datetime
    description: str
    status: OperationStatus
    request_id: str | None
    triggered_by: str | None
    acted_as: uuid.UUID | None
    duration: timedelta | None

    @classmethod
    @abstractmethod
    def action_kind(cls) -> ActionKind:
        raise NotImplementedError

    @override
    def sidecar_id(self, row: AuditLogRow) -> AuditLogID:
        return AuditLogID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: AuditLogRow) -> AuditLogData:
        return row.to_dataclass()

    def _build_row(
        self,
        *,
        entity_id: EntityID | str | None = None,
        lookup_kind: str | None = None,
        lookup_key: str | None = None,
    ) -> AuditLogRow:
        return AuditLogRow(
            action_id=self.action_id,
            action_kind=self.action_kind(),
            action_name=self.action_name,
            entity_type=self.entity_type,
            operation=self.operation,
            created_at=self.created_at,
            description=self.description,
            status=self.status,
            entity_id=None if entity_id is None else str(entity_id),
            lookup_kind=lookup_kind,
            lookup_key=lookup_key,
            request_id=self.request_id,
            triggered_by=self.triggered_by,
            acted_as=self.acted_as,
            duration=self.duration,
        )


@dataclass
class SingleEntityAuditLogCreator(AuditLogCreator):
    entity_id: EntityID

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.SINGLE_ENTITY

    @override
    def build_row(self) -> AuditLogRow:
        return self._build_row(entity_id=self.entity_id)


@dataclass
class BulkAuditLogCreator(AuditLogCreator):
    entity_id: EntityID

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.BULK

    @override
    def build_row(self) -> AuditLogRow:
        return self._build_row(entity_id=self.entity_id)


@dataclass
class ScopeAuditLogCreator(AuditLogCreator):
    """One entity a scope action affected; ``None`` when it affected nothing.

    The scopes go to ``audit_log_scopes`` via :class:`AuditLogScopeCreator`.
    """

    entity_id: EntityID | None

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.SCOPE

    @override
    def build_row(self) -> AuditLogRow:
        return self._build_row(entity_id=self.entity_id)


@dataclass
class LookupAuditLogCreator(AuditLogCreator):
    lookup_kind: str
    lookup_key: str
    entity_id: EntityID | None

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.LOOKUP

    @override
    def build_row(self) -> AuditLogRow:
        return self._build_row(
            entity_id=self.entity_id,
            lookup_kind=self.lookup_kind,
            lookup_key=self.lookup_key,
        )


@dataclass
class GlobalAuditLogCreator(AuditLogCreator):
    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.GLOBAL

    @override
    def build_row(self) -> AuditLogRow:
        return self._build_row()


@dataclass
class LegacyAuditLogCreator(AuditLogCreator):
    """An action on the legacy ``BaseAction`` base, which declares no shape.

    ``entity_id`` is whatever the runner resolved, often nothing. Goes away with
    the legacy base.
    """

    entity_id: str | None

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.UNKNOWN

    @override
    def build_row(self) -> AuditLogRow:
        return self._build_row(entity_id=self.entity_id)


@dataclass
class AuditLogScopeCreator(SidecarFieldCreator[AuditLogID, AuditLogScopeRow, AuditLogScopeData]):
    """A scope the audited run covered, owned by the audit row it is written under."""

    scope_type: str
    scope_id: ScopeID

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: AuditLogID) -> AuditLogScopeRow:
        return AuditLogScopeRow(
            audit_log_id=owner_id,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
        )

    @override
    def to_data(self, row: AuditLogScopeRow) -> AuditLogScopeData:
        return AuditLogScopeData(
            audit_log_id=AuditLogID(row.audit_log_id),
            scope_type=row.scope_type,
            scope_id=row.scope_id,
        )
