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
from ai.backend.common.data.entity.types import EntityID, EntityIdentifier, EntityType, ScopeID
from ai.backend.manager.actions.types import ActionKind, OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogScopeData
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.specs.creator import (
    DanglingFieldCreator,
    FieldCreator,
    NestedFieldCreator,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

__all__ = (
    "BaseAuditLogFields",
    "OwnedAuditLogCreator",
    "DanglingAuditLogCreator",
    "SingleEntityAuditLogCreator",
    "BulkAuditLogCreator",
    "ScopeAuditLogCreator",
    "LookupAuditLogCreator",
    "MissedLookupAuditLogCreator",
    "EmptyScopeAuditLogCreator",
    "RelationAuditLogCreator",
    "GlobalAuditLogCreator",
    "LegacyAuditLogCreator",
    "AuditLogScopeCreator",
)


@dataclass
class BaseAuditLogFields:
    """Columns every audit row is written with, whoever owns it.

    Subclasses add the one target field their shape has and declare their
    ``action_kind``, so neither is something a writer can get wrong.
    """

    action_id: ActionID
    operation: str
    action_name: str
    created_at: datetime
    description: str
    status: OperationStatus
    request_id: str | None
    triggered_by: str | None
    acted_as: uuid.UUID | None
    duration: timedelta | None
    client_ip: str | None

    @classmethod
    @abstractmethod
    def action_kind(cls) -> ActionKind:
        raise NotImplementedError

    def field_id(self, row: AuditLogRow) -> AuditLogID:
        return row.id

    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    def to_data(self, row: AuditLogRow) -> AuditLogData:
        return row.to_dataclass()

    def _build_row(
        self,
        *,
        entity_type: str | None,
        entity_id: EntityID | str | None = None,
        lookup_kind: str | None = None,
        lookup_key: str | None = None,
    ) -> AuditLogRow:
        return AuditLogRow(
            action_id=self.action_id,
            action_kind=self.action_kind(),
            action_name=self.action_name,
            entity_type=entity_type,
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
            client_ip=self.client_ip,
        )


@dataclass
class OwnedAuditLogCreator(
    BaseAuditLogFields, FieldCreator[EntityIdentifier, AuditLogRow, AuditLogData]
):
    """A record of what an operation did to one entity, written under that entity.

    The entity columns come from the owner handed in, so nothing carries its type as a
    loose string.
    """

    @override
    def build_row(self, owner_id: EntityIdentifier) -> AuditLogRow:
        return self._build_row(entity_type=owner_id.entity_type(), entity_id=owner_id)


@dataclass
class DanglingAuditLogCreator(BaseAuditLogFields, DanglingFieldCreator[AuditLogRow, AuditLogData]):
    """A record of an operation that named no entity, so the row has no id.

    ``entity_type`` is the kind it was about, or ``None`` where the operation named no
    kind either — a relation stands between two entities and is neither of them.
    """

    entity_type: EntityType | None

    @override
    def build_row(self) -> AuditLogRow:
        return self._build_row(entity_type=self.entity_type, entity_id=None)


@dataclass
class SingleEntityAuditLogCreator(OwnedAuditLogCreator):
    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.SINGLE_ENTITY


@dataclass
class BulkAuditLogCreator(OwnedAuditLogCreator):
    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.BULK


@dataclass
class ScopeAuditLogCreator(OwnedAuditLogCreator):
    """One entity a scope action affected.

    The scopes go to ``audit_log_scopes`` via :class:`AuditLogScopeCreator`; a run that
    affected nothing is recorded by :class:`EmptyScopeAuditLogCreator` instead.
    """

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.SCOPE


@dataclass
class LookupAuditLogCreator(OwnedAuditLogCreator):
    """A key that resolved, recorded against what it named."""

    lookup_kind: str
    lookup_key: str

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.LOOKUP

    @override
    def build_row(self, owner_id: EntityIdentifier) -> AuditLogRow:
        return self._build_row(
            entity_type=owner_id.entity_type(),
            entity_id=owner_id,
            lookup_kind=self.lookup_kind,
            lookup_key=self.lookup_key,
        )


@dataclass
class MissedLookupAuditLogCreator(DanglingAuditLogCreator):
    """A key that named nothing, so only the key itself identifies the row."""

    lookup_kind: str
    lookup_key: str

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.LOOKUP

    @override
    def build_row(self) -> AuditLogRow:
        return self._build_row(
            entity_type=self.entity_type,
            entity_id=None,
            lookup_kind=self.lookup_kind,
            lookup_key=self.lookup_key,
        )


@dataclass
class EmptyScopeAuditLogCreator(DanglingAuditLogCreator):
    """A scope run that affected no entity, which still has to leave a trace."""

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.SCOPE


@dataclass
class RelationAuditLogCreator(DanglingAuditLogCreator):
    """A run that linked or unlinked two entities.

    Names no entity kind: what it wrote stands between two entities and is neither of
    them. The scopes it was about go to ``audit_log_scopes``.
    """

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.RELATION


@dataclass
class GlobalAuditLogCreator(DanglingAuditLogCreator):
    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.GLOBAL


@dataclass
class LegacyAuditLogCreator(DanglingAuditLogCreator):
    """An action on the legacy ``BaseAction`` base, which declares no shape.

    ``entity_id`` is whatever the runner resolved, often nothing. Goes away with
    the legacy base.
    """

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.UNKNOWN


@dataclass
class AuditLogScopeCreator(NestedFieldCreator[AuditLogID, AuditLogScopeRow, AuditLogScopeData]):
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
