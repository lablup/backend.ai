from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.actions.v2.ops.base import BulkLookupEntityOpsAction
from ai.backend.manager.models.user.lookups import UserEmailsLookup
from ai.backend.manager.services.user.actions.lookup import UserEmailKey


@dataclass
class BulkLookupUsersAction(BulkLookupEntityOpsAction[str, UserID]):
    """Resolve several emails into the users they name."""

    emails: Sequence[str]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_lookup_users"

    @override
    def keys(self) -> Sequence[str]:
        return tuple(self.emails)

    @override
    def to_lookup_key(self, key: str) -> UserEmailKey:
        return UserEmailKey(email=key)

    @override
    def to_lookup(self) -> UserEmailsLookup:
        return UserEmailsLookup()
