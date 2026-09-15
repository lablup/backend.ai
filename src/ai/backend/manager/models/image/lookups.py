"""Read specs for image aliases."""

from __future__ import annotations

from collections.abc import Sequence
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.manager.models.image.row import ImageAliasRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class ImageAliasOwnerLookup(FieldOwnerLookup[ImageAliasID, ImageID]):
    """The image an alias belongs to."""

    @override
    def build_query(
        self, field_ids: Sequence[ImageAliasID]
    ) -> sa.sql.Select[tuple[ImageAliasID, ImageID]]:
        return sa.select(ImageAliasRow.id, ImageAliasRow.image_id).where(
            ImageAliasRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> ImageID:
        return ImageID(value)
