from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.image.types import ImageAliasData
from ai.backend.manager.models.image.queriers import BulkImageAliasQuerier
from ai.backend.manager.models.image.row import ImageAliasRow
from ai.backend.manager.services.image.actions.lookup_alias_owner import (
    LookupBulkImageAliasOwnerAction,
)


@dataclass
class BulkGetImageAliasesAction(
    PartialBulkGetFieldOpsAction[ImageAliasID, ImageID, ImageAliasRow, ImageAliasData]
):
    """Read the image aliases the caller named, answering for each one."""

    ids: Sequence[ImageAliasID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_image_aliases"

    @override
    def field_ids(self) -> Sequence[ImageAliasID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkImageAliasOwnerAction:
        return LookupBulkImageAliasOwnerAction(alias_ids=self.ids)

    @override
    def to_querier(self) -> BulkImageAliasQuerier:
        return BulkImageAliasQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[ImageAliasID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
