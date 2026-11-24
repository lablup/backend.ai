"""The lookups reading the user an SSH keypair belongs to."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.ssh_keypair.lookups import SSHKeypairOwnerLookup


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
