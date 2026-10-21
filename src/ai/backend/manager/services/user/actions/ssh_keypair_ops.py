"""Service actions for the SSH keypair a user owns."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, final, override

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
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
class SearchSSHKeypairsAction(OperationScopeOpsAction[SSHKeypairRow, SSHKeypairData]):
    """Page through the SSH keypairs a user owns."""

    user_id: UserID
    searcher: SSHKeypairSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.user_id,)

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (UserSSHKeypairTarget(user_uuid=self.user_id),)

    @override
    def to_searcher(self) -> SSHKeypairSearcher:
        return self.searcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_ssh_keypairs"
