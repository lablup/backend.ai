from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkRuntimeFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupRuntimeFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.dotfile.lookups import DotfileOwnerLookup


@dataclass(frozen=True)
class DotfileIDLookupKey(LookupKey):
    """A dotfile's id, resolved into the entity it belongs to."""

    dotfile_id: DotfileID

    @override
    def kind(self) -> str:
        return "dotfile_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.dotfile_id)}


@dataclass
class LookupDotfileOwnerAction(LookupRuntimeFieldOwnerOpsAction[DotfileID]):
    """The entity one dotfile belongs to; its kind is a value on the row."""

    dotfile_id: DotfileID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_dotfile_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return DotfileIDLookupKey(self.dotfile_id)

    @override
    def field_id(self) -> DotfileID:
        return self.dotfile_id

    @override
    def to_owner_lookup(self) -> DotfileOwnerLookup:
        return DotfileOwnerLookup()


@dataclass
class LookupBulkDotfileOwnerAction(LookupBulkRuntimeFieldOwnerOpsAction[DotfileID]):
    """The entities several dotfiles belong to."""

    dotfile_ids: Sequence[DotfileID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_dotfile_owner"

    @override
    def to_lookup_key(self, field_id: DotfileID) -> LookupKey:
        return DotfileIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[DotfileID]:
        return tuple(self.dotfile_ids)

    @override
    def to_owner_lookup(self) -> DotfileOwnerLookup:
        return DotfileOwnerLookup()
