"""Owner candidates of audit records."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.base import GUID, EntityTypeColumn
from ai.backend.manager.models.specs.owner_candidates import FieldOwnerCandidates

__all__ = ("AuditLogOwnerCandidates",)

_UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


class AuditLogOwnerCandidates(FieldOwnerCandidates[AuditLogID]):
    """The entity a record is about, each scope it recorded, and the user who triggered
    it."""

    @override
    def owners_of(
        self, field_ids: Sequence[AuditLogID]
    ) -> Sequence[sa.sql.Select[tuple[AuditLogID, uuid.UUID, EntityType]]]:
        # The filter drops the nulls; type_coerce states that to the type checker.
        entity = sa.select(
            AuditLogRow.id,
            sa.type_coerce(AuditLogRow.entity_id, GUID[uuid.UUID]()),
            sa.type_coerce(AuditLogRow.entity_type, EntityTypeColumn()),
        ).where(
            AuditLogRow.id.in_(field_ids),
            AuditLogRow.entity_id.is_not(None),
            AuditLogRow.entity_type.is_not(None),
        )
        scopes = sa.select(
            AuditLogScopeRow.audit_log_id,
            AuditLogScopeRow.scope_id,
            AuditLogScopeRow.scope_type,
        ).where(AuditLogScopeRow.audit_log_id.in_(field_ids))
        triggered_by = sa.select(
            AuditLogRow.id,
            sa.cast(AuditLogRow.triggered_by, GUID[uuid.UUID]()),
            sa.literal(UserEntityType(), EntityTypeColumn()),
        ).where(
            AuditLogRow.id.in_(field_ids),
            AuditLogRow.triggered_by.op("~")(_UUID_PATTERN),
        )
        return [entity, scopes, triggered_by]
