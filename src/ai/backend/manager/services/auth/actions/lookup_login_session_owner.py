from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.login_session import LoginSessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.login_session.lookups import LoginSessionOwnerLookup


@dataclass(frozen=True)
class LoginSessionIDLookupKey(LookupKey):
    """A session's id, resolved into the user it belongs to."""

    session_id: LoginSessionID

    @override
    def kind(self) -> str:
        return "login_session_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.session_id)}


@dataclass
class LookupLoginSessionOwnerAction(LookupFieldOwnerOpsAction[LoginSessionID, UserID]):
    """The user a login session belongs to."""

    session_id: LoginSessionID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_login_session_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return LoginSessionIDLookupKey(self.session_id)

    @override
    def field_id(self) -> LoginSessionID:
        return self.session_id

    @override
    def to_owner_lookup(self) -> LoginSessionOwnerLookup:
        return LoginSessionOwnerLookup()


@dataclass
class LookupBulkLoginSessionOwnerAction(LookupBulkFieldOwnerOpsAction[LoginSessionID, UserID]):
    """The users several login sessions belong to."""

    session_ids: Sequence[LoginSessionID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_login_session_owner"

    @override
    def to_lookup_key(self, field_id: LoginSessionID) -> LookupKey:
        return LoginSessionIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[LoginSessionID]:
        return tuple(self.session_ids)

    @override
    def to_owner_lookup(self) -> LoginSessionOwnerLookup:
        return LoginSessionOwnerLookup()
