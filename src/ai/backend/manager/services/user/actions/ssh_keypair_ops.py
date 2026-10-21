"""Service actions for the SSH keypair a user owns."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.ssh_keypair.lookups import SSHKeypairOwnerLookup
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.models.ssh_keypair.scopes import UserSSHKeypairTarget
from ai.backend.manager.models.ssh_keypair.searchers import SSHKeypairSearcher


@dataclass(frozen=True)
class SSHKeypairIDLookupKey(LookupKey):
    """An SSH keypair row's id, resolved into the user that owns it."""

    ssh_keypair_id: SSHKeypairID

    @override
    def kind(self) -> str:
        return "ssh_keypair_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.ssh_keypair_id)}


@dataclass
class LookupSSHKeypairOwnerAction(LookupFieldOwnerOpsAction[SSHKeypairID, UserID]):
    """The user an SSH keypair belongs to."""

    ssh_keypair_id: SSHKeypairID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_ssh_keypair_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return SSHKeypairIDLookupKey(self.ssh_keypair_id)

    @override
    def field_id(self) -> SSHKeypairID:
        return self.ssh_keypair_id

    @override
    def to_owner_lookup(self) -> SSHKeypairOwnerLookup:
        return SSHKeypairOwnerLookup()


@dataclass
class LookupBulkSSHKeypairOwnerAction(LookupBulkFieldOwnerOpsAction[SSHKeypairID, UserID]):
    """The users several SSH keypairs belong to."""

    ssh_keypair_ids: Sequence[SSHKeypairID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_ssh_keypair_owner"

    @override
    def to_lookup_key(self, field_id: SSHKeypairID) -> LookupKey:
        return SSHKeypairIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[SSHKeypairID]:
        return tuple(self.ssh_keypair_ids)

    @override
    def to_owner_lookup(self) -> SSHKeypairOwnerLookup:
        return SSHKeypairOwnerLookup()


@dataclass(frozen=True)
class SearchSSHKeypairsAction(BulkScopedSearchOpsAction[SSHKeypairRow, SSHKeypairData]):
    """Page through the SSH keypairs of the users named, combined with OR."""

    user_ids: Sequence[UserID]
    searcher: SSHKeypairSearcher

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.user_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [UserSSHKeypairTarget(user_uuid=user_id) for user_id in self.user_ids]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_ssh_keypairs"

    @override
    def to_searcher(self) -> SSHKeypairSearcher:
        return self.searcher
