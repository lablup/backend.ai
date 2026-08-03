from __future__ import annotations

import uuid
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import override

from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.manager.actions.types import ActionKind, OperationStatus
from ai.backend.manager.models.audit_log import AuditLogRow, AuditLogScopeRow
from ai.backend.manager.repositories.base import CreatorSpec, DependentCreatorSpec

__all__ = (
    "AuditLogCreatorSpec",
    "SingleEntityAuditLogCreatorSpec",
    "BulkAuditLogCreatorSpec",
    "ScopeAuditLogCreatorSpec",
    "LookupAuditLogCreatorSpec",
    "GlobalAuditLogCreatorSpec",
    "LegacyAuditLogCreatorSpec",
    "AuditLogScopeCreatorSpec",
)


@dataclass
class AuditLogCreatorSpec(CreatorSpec[AuditLogRow]):
    """Fields every audit row is written with.

    Subclasses add the one target field their shape has and declare their
    ``action_kind``, so neither is something a writer can get wrong.
    """

    action_id: uuid.UUID
    entity_type: str
    operation: str
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
            entity_type=self.entity_type,
            operation=self.operation,
            created_at=self.created_at,
            description=self.description,
            status=self.status,
            entity_id=entity_id,
            lookup_kind=lookup_kind,
            lookup_key=lookup_key,
            request_id=self.request_id,
            triggered_by=self.triggered_by,
            acted_as=self.acted_as,
            duration=self.duration,
        )


@dataclass
class SingleEntityAuditLogCreatorSpec(AuditLogCreatorSpec):
    entity_id: EntityID

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.SINGLE_ENTITY

    @override
    def build_row(self) -> AuditLogRow:
        return self._build_row(entity_id=self.entity_id)


@dataclass
class BulkAuditLogCreatorSpec(AuditLogCreatorSpec):
    entity_id: EntityID

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.BULK

    @override
    def build_row(self) -> AuditLogRow:
        return self._build_row(entity_id=self.entity_id)


@dataclass
class ScopeAuditLogCreatorSpec(AuditLogCreatorSpec):
    """One entity a scope action affected; ``None`` when it affected nothing.

    The scopes go to ``audit_log_scopes`` via :class:`AuditLogScopeCreatorSpec`.
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
class LookupAuditLogCreatorSpec(AuditLogCreatorSpec):
    lookup_kind: str
    lookup_key: str

    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.LOOKUP

    @override
    def build_row(self) -> AuditLogRow:
        return self._build_row(lookup_kind=self.lookup_kind, lookup_key=self.lookup_key)


@dataclass
class GlobalAuditLogCreatorSpec(AuditLogCreatorSpec):
    @classmethod
    @override
    def action_kind(cls) -> ActionKind:
        return ActionKind.GLOBAL

    @override
    def build_row(self) -> AuditLogRow:
        return self._build_row()


@dataclass
class LegacyAuditLogCreatorSpec(AuditLogCreatorSpec):
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
class AuditLogScopeCreatorSpec(DependentCreatorSpec[uuid.UUID, AuditLogScopeRow]):
    """A scope of the audited entity, attached to its audit row once that row exists."""

    scope_type: str
    scope_id: ScopeID

    @override
    def build_row(self, dependency: uuid.UUID) -> AuditLogScopeRow:
        return AuditLogScopeRow(
            audit_log_id=dependency,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
        )
