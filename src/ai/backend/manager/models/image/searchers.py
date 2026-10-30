"""List-read specs for images."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import Any, Final, override

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.data.image.types import ImageAliasData, ImageData, ImageStatus
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_and, combine_conditions_or
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.image.searchable_fields import (
    ImageAliasSearchableFields,
    ImageSearchableFields,
)
from ai.backend.manager.models.specs.orders.condition import ConditionOrder
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.specs.searcher import Searcher

AMBIGUITY_PROBE: Final[int] = 2
"""One row more than a read expecting a single image needs."""


@dataclass
class ImageSearcher(Searcher[ImageRow, ImageData]):
    """Images matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ImageRow)

    @override
    def to_data(self, row: ImageRow) -> ImageData:
        return ImageSearchableFields.own.to_data(row)


@dataclass
class ImageAliasSearcher(Searcher[ImageAliasRow, ImageAliasData]):
    """Image aliases matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ImageAliasRow)

    @override
    def to_data(self, row: ImageAliasRow) -> ImageAliasData:
        return ImageAliasSearchableFields.own.to_data(row)


class ImageLookupSearcher(ImageSearcher):
    """Reads the one image a name points at. The pieces every such read is built from.

    ``images`` holds no unique key over a canonical name and architecture, so the order
    decides which row answers: a live image before a deleted one, an older before a newer.
    The page holds :data:`AMBIGUITY_PROBE` rows rather than one, so a caller expecting a
    single image can say the name matched several instead of answering as if it had not.
    """

    def _canonical_match(self, canonical: str, architecture: str) -> QueryCondition:
        fields = ImageSearchableFields.own
        return combine_conditions_and([
            fields.name.filter.equals(self._exact(canonical)),
            fields.architecture.filter.equals(self._exact(architecture)),
        ])

    def _alias_match(self, alias: str) -> QueryCondition:
        alias_field = ImageAliasSearchableFields.own.alias
        return ImageSearchableFields.nested.aliases.correlation.some([
            alias_field.filter.equals(self._exact(alias))
        ])

    def _status_conditions(self, statuses: Collection[ImageStatus]) -> list[QueryCondition]:
        """An empty collection allows every status."""
        if not statuses:
            return []
        return [ImageSearchableFields.own.status.filter.in_(statuses)]

    def _alive_then_oldest(self) -> list[QueryOrder]:
        fields = ImageSearchableFields.own
        alive = fields.status.filter.equals(ImageStatus.ALIVE)
        return [ConditionOrder(alive).first(), fields.created_at.order.apply(ascending=True)]

    def _exact(self, value: str) -> StringMatchSpec:
        return StringMatchSpec(value=value, case_insensitive=False, negated=False)


class CanonicalImageSearcher(ImageLookupSearcher):
    """The one image a canonical name and architecture point at."""

    def __init__(
        self, canonical: str, architecture: str, statuses: Collection[ImageStatus]
    ) -> None:
        super().__init__(
            pagination=OffsetPagination(limit=AMBIGUITY_PROBE),
            conditions=[
                self._canonical_match(canonical, architecture),
                *self._status_conditions(statuses),
            ],
            orders=self._alive_then_oldest(),
        )


class ReferenceImageSearcher(ImageLookupSearcher):
    """The one image a reference points at, read as a canonical for the architecture or as
    an alias of any architecture. A canonical match answers before an alias match."""

    def __init__(
        self, reference: str, architecture: str, statuses: Collection[ImageStatus]
    ) -> None:
        canonical_match = self._canonical_match(reference, architecture)
        super().__init__(
            pagination=OffsetPagination(limit=AMBIGUITY_PROBE),
            conditions=[
                combine_conditions_or([canonical_match, self._alias_match(reference)]),
                *self._status_conditions(statuses),
            ],
            orders=[ConditionOrder(canonical_match).first(), *self._alive_then_oldest()],
        )


class AliasedImageSearcher(ImageLookupSearcher):
    """The one image an alias points at."""

    def __init__(self, alias: str, statuses: Collection[ImageStatus]) -> None:
        super().__init__(
            pagination=OffsetPagination(limit=AMBIGUITY_PROBE),
            conditions=[self._alias_match(alias), *self._status_conditions(statuses)],
            orders=self._alive_then_oldest(),
        )
