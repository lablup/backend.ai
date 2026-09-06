from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.login_history import LoginHistoryID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.login_session.lookups import LoginHistoryOwnerLookup


@dataclass(frozen=True)
class LoginHistoryIDLookupKey(LookupKey):
    """An attempt's id, resolved into the user it was recorded against."""

    attempt_id: LoginHistoryID

    @override
    def kind(self) -> str:
        return "login_history_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.attempt_id)}


@dataclass
class LookupLoginHistoryOwnerAction(LookupFieldOwnerOpsAction[LoginHistoryID, UserID]):
    """The user a login attempt was recorded against."""

    attempt_id: LoginHistoryID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_login_history_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return LoginHistoryIDLookupKey(self.attempt_id)

    @override
    def field_id(self) -> LoginHistoryID:
        return self.attempt_id

    @override
    def to_owner_lookup(self) -> LoginHistoryOwnerLookup:
        return LoginHistoryOwnerLookup()


@dataclass
class LookupBulkLoginHistoryOwnerAction(LookupBulkFieldOwnerOpsAction[LoginHistoryID, UserID]):
    """The users several login attempts were recorded against."""

    attempt_ids: Sequence[LoginHistoryID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_login_history_owner"

    @override
    def to_lookup_key(self, field_id: LoginHistoryID) -> LookupKey:
        return LoginHistoryIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[LoginHistoryID]:
        return tuple(self.attempt_ids)

    @override
    def to_owner_lookup(self) -> LoginHistoryOwnerLookup:
        return LoginHistoryOwnerLookup()
