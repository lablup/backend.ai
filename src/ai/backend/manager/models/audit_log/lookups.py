"""Read specs for audit records."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType, RuntimeEntityID
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.specs.lookup import RuntimeFieldOwnerLookup

__all__ = ("AuditLogOwnerLookup",)

_UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
_NIL_UUID = "00000000-0000-0000-0000-000000000000"


class AuditLogOwnerLookup(RuntimeFieldOwnerLookup[AuditLogID]):
    """The entity each of the records named is about.

    A record naming no entity by uuid is answered for by the global entity, so only a
    superadmin reads it.
    """

    @override
    def build_query(self, field_ids: Sequence[AuditLogID]) -> sa.sql.Select[Any]:
        has_owner = sa.and_(
            AuditLogRow.entity_type.is_not(None),
            AuditLogRow.entity_id.op("~")(_UUID_PATTERN),
        )
        return sa.select(
            AuditLogRow.id,
            sa.case(
                (has_owner, sa.cast(AuditLogRow.entity_id, GUID)),
                else_=sa.cast(sa.literal(_NIL_UUID), GUID),
            ),
            sa.case(
                (has_owner, AuditLogRow.entity_type),
                else_=sa.literal(GlobalEntityType.name()),
            ),
        ).where(AuditLogRow.id.in_(field_ids))

    @override
    def owner_of(self, entity_type: EntityType, entity_id: UUID) -> RuntimeEntityID:
        return RuntimeEntityID(entity_type, entity_id)
