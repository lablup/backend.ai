from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.error_log import ErrorLogID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.error_log.lookups import ErrorLogOwnerLookup


@dataclass(frozen=True)
class ErrorLogIDLookupKey(LookupKey):
    """A log's id, resolved into the user it was recorded against."""

    log_id: ErrorLogID

    @override
    def kind(self) -> str:
        return "error_log_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.log_id)}


@dataclass
class LookupErrorLogOwnerAction(LookupFieldOwnerOpsAction[ErrorLogID, UserID]):
    """The user an error was recorded against."""

    log_id: ErrorLogID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_error_log_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return ErrorLogIDLookupKey(self.log_id)

    @override
    def field_id(self) -> ErrorLogID:
        return self.log_id

    @override
    def to_owner_lookup(self) -> ErrorLogOwnerLookup:
        return ErrorLogOwnerLookup()


@dataclass
class LookupBulkErrorLogOwnerAction(LookupBulkFieldOwnerOpsAction[ErrorLogID, UserID]):
    """The users several errors were recorded against."""

    log_ids: Sequence[ErrorLogID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_error_log_owner"

    @override
    def to_lookup_key(self, field_id: ErrorLogID) -> LookupKey:
        return ErrorLogIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[ErrorLogID]:
        return tuple(self.log_ids)

    @override
    def to_owner_lookup(self) -> ErrorLogOwnerLookup:
        return ErrorLogOwnerLookup()
