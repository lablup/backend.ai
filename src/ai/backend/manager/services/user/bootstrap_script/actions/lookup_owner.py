from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.bootstrap_script.lookups import BootstrapScriptOwnerLookup


@dataclass(frozen=True)
class BootstrapScriptIDLookupKey(LookupKey):
    """A bootstrap script's id, resolved into the user it is set on."""

    script_id: BootstrapScriptID

    @override
    def kind(self) -> str:
        return "bootstrap_script_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.script_id)}


@dataclass
class LookupBootstrapScriptOwnerAction(LookupFieldOwnerOpsAction[BootstrapScriptID, UserID]):
    """The user a bootstrap script is set on."""

    script_id: BootstrapScriptID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bootstrap_script_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return BootstrapScriptIDLookupKey(self.script_id)

    @override
    def field_id(self) -> BootstrapScriptID:
        return self.script_id

    @override
    def to_owner_lookup(self) -> BootstrapScriptOwnerLookup:
        return BootstrapScriptOwnerLookup()


@dataclass
class LookupBulkBootstrapScriptOwnerAction(
    LookupBulkFieldOwnerOpsAction[BootstrapScriptID, UserID]
):
    """The users several bootstrap scripts are set on."""

    script_ids: Sequence[BootstrapScriptID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_bootstrap_script_owner"

    @override
    def to_lookup_key(self, field_id: BootstrapScriptID) -> LookupKey:
        return BootstrapScriptIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[BootstrapScriptID]:
        return tuple(self.script_ids)

    @override
    def to_owner_lookup(self) -> BootstrapScriptOwnerLookup:
        return BootstrapScriptOwnerLookup()
