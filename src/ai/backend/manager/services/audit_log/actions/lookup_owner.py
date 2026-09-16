from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import (
    LookupBulkRuntimeFieldOwnerOpsAction,
)
from ai.backend.manager.actions.v2.field.lookup import LookupRuntimeFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.audit_log.lookups import AuditLogOwnerLookup


@dataclass(frozen=True)
class AuditLogIDLookupKey(LookupKey):
    """A record's id, resolved into the entity it is about."""

    audit_log_id: AuditLogID

    @override
    def kind(self) -> str:
        return "audit_log_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.audit_log_id)}


@dataclass
class LookupAuditLogOwnerAction(LookupRuntimeFieldOwnerOpsAction[AuditLogID]):
    """The entity one record is about.

    Records the run rather than gating it: the operation that follows is authorized
    against the entity this answers with.
    """

    audit_log_id: AuditLogID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_audit_log_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return AuditLogIDLookupKey(self.audit_log_id)

    @override
    def field_id(self) -> AuditLogID:
        return self.audit_log_id

    @override
    def to_owner_lookup(self) -> AuditLogOwnerLookup:
        return AuditLogOwnerLookup()


@dataclass
class LookupBulkAuditLogOwnerAction(LookupBulkRuntimeFieldOwnerOpsAction[AuditLogID]):
    """The entities several records are about."""

    audit_log_ids: Sequence[AuditLogID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_audit_log_owner"

    @override
    def to_lookup_key(self, field_id: AuditLogID) -> LookupKey:
        return AuditLogIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[AuditLogID]:
        return tuple(self.audit_log_ids)

    @override
    def to_owner_lookup(self) -> AuditLogOwnerLookup:
        return AuditLogOwnerLookup()
