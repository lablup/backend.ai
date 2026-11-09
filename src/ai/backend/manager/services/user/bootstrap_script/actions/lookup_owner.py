from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkRuntimeFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupRuntimeFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.bootstrap_script.lookups import BootstrapScriptOwnerLookup


@dataclass(frozen=True)
class BootstrapScriptIDLookupKey(LookupKey):
    """A bootstrap script's id, resolved into the entity it is set on."""

    script_id: BootstrapScriptID

    @override
    def kind(self) -> str:
        return "bootstrap_script_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.script_id)}


@dataclass
class LookupBootstrapScriptOwnerAction(LookupRuntimeFieldOwnerOpsAction[BootstrapScriptID]):
    """The entity a bootstrap script is set on; its kind is a value on the row."""

    script_id: BootstrapScriptID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

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
class LookupBulkBootstrapScriptOwnerAction(LookupBulkRuntimeFieldOwnerOpsAction[BootstrapScriptID]):
    """The entities several bootstrap scripts are set on."""

    script_ids: Sequence[BootstrapScriptID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

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
