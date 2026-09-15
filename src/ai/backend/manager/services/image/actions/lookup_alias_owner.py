from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.image import ImageEntityType, ImageID
from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.image.lookups import ImageAliasOwnerLookup


@dataclass(frozen=True)
class ImageAliasIDLookupKey(LookupKey):
    """An alias's id, resolved into the image it belongs to."""

    alias_id: ImageAliasID

    @override
    def kind(self) -> str:
        return "image_alias_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.alias_id)}


@dataclass
class LookupImageAliasOwnerAction(LookupFieldOwnerOpsAction[ImageAliasID, ImageID]):
    """The image an alias belongs to."""

    alias_id: ImageAliasID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ImageEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_image_alias_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return ImageAliasIDLookupKey(self.alias_id)

    @override
    def field_id(self) -> ImageAliasID:
        return self.alias_id

    @override
    def to_owner_lookup(self) -> ImageAliasOwnerLookup:
        return ImageAliasOwnerLookup()


@dataclass
class LookupBulkImageAliasOwnerAction(LookupBulkFieldOwnerOpsAction[ImageAliasID, ImageID]):
    """The images several aliases belong to."""

    alias_ids: Sequence[ImageAliasID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ImageEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_image_alias_owner"

    @override
    def to_lookup_key(self, field_id: ImageAliasID) -> LookupKey:
        return ImageAliasIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[ImageAliasID]:
        return tuple(self.alias_ids)

    @override
    def to_owner_lookup(self) -> ImageAliasOwnerLookup:
        return ImageAliasOwnerLookup()
