"""One searchable-field declaration written the way an entity writes its own.

``own`` connects the shelf's columns, ``nested`` reaches the related rows through a
correlation, and ``linked`` declares the entity whose use narrows a search. The
declaration adds no behavior: what the tests around it check is the shared
implementation these slots hand the columns to.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget
from ai.backend.manager.models.specs.conditions.array import ArrayConditions
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.number import DecimalConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation, ToOneCorrelation
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField
from ai.backend.manager.models.specs.search.usage import UsageConditions
from ai.backend.manager.models.specs.searcher import Searcher

from .shelf_rows import (
    BoxData,
    BoxRow,
    BoxState,
    CartID,
    CartLineRow,
    CategoryData,
    CategoryRow,
    ShelfData,
    ShelfItemData,
    ShelfItemRow,
    ShelfKind,
    ShelfRow,
    SpecData,
    SpecRow,
    ZoneID,
)


class _CategoryOwnFields(RowDataConverter[CategoryRow, CategoryData]):
    id = SearchableField(
        CategoryRow.id, UUIDConditions(CategoryRow.id), ColumnOrder(CategoryRow.id)
    )
    title = SearchableField(
        CategoryRow.title, StringConditions(CategoryRow.title), ColumnOrder(CategoryRow.title)
    )
    rank = SearchableField(
        CategoryRow.rank, IntConditions(CategoryRow.rank), ColumnOrder(CategoryRow.rank)
    )

    @override
    def to_data(self, row: CategoryRow) -> CategoryData:
        return CategoryData(
            id=self.id.read(row),
            title=self.title.read(row),
            rank=self.rank.read(row),
        )


class CategorySearchableFields:
    own = _CategoryOwnFields()


class _SpecOwnFields(RowDataConverter[SpecRow, SpecData]):
    id = SearchableField(SpecRow.id, UUIDConditions(SpecRow.id), ColumnOrder(SpecRow.id))
    shelf_id = SearchableField(
        SpecRow.shelf_id, UUIDConditions(SpecRow.shelf_id), ColumnOrder(SpecRow.shelf_id)
    )
    grade = SearchableField(
        SpecRow.grade, StringConditions(SpecRow.grade), ColumnOrder(SpecRow.grade)
    )
    weight = SearchableField(
        SpecRow.weight, IntConditions(SpecRow.weight), ColumnOrder(SpecRow.weight)
    )

    @override
    def to_data(self, row: SpecRow) -> SpecData:
        return SpecData(
            id=self.id.read(row),
            shelf_id=self.shelf_id.read(row),
            grade=self.grade.read(row),
            weight=self.weight.read(row),
        )


class SpecSearchableFields:
    own = _SpecOwnFields()


class _ShelfItemOwnFields(RowDataConverter[ShelfItemRow, ShelfItemData]):
    id = SearchableField(
        ShelfItemRow.id, UUIDConditions(ShelfItemRow.id), ColumnOrder(ShelfItemRow.id)
    )
    box_id = SearchableField(
        ShelfItemRow.box_id, UUIDConditions(ShelfItemRow.box_id), ColumnOrder(ShelfItemRow.box_id)
    )
    code = SearchableField(
        ShelfItemRow.code, StringConditions(ShelfItemRow.code), ColumnOrder(ShelfItemRow.code)
    )
    qty = SearchableField(
        ShelfItemRow.qty, IntConditions(ShelfItemRow.qty), ColumnOrder(ShelfItemRow.qty)
    )

    @override
    def to_data(self, row: ShelfItemRow) -> ShelfItemData:
        return ShelfItemData(
            id=self.id.read(row),
            box_id=self.box_id.read(row),
            code=self.code.read(row),
            qty=self.qty.read(row),
        )


class ShelfItemSearchableFields:
    own = _ShelfItemOwnFields()


class _BoxOwnFields(RowDataConverter[BoxRow, BoxData]):
    id = SearchableField(BoxRow.id, UUIDConditions(BoxRow.id), ColumnOrder(BoxRow.id))
    shelf_id = SearchableField(
        BoxRow.shelf_id, UUIDConditions(BoxRow.shelf_id), ColumnOrder(BoxRow.shelf_id)
    )
    label = SearchableField(BoxRow.label, StringConditions(BoxRow.label), ColumnOrder(BoxRow.label))
    size = SearchableField(BoxRow.size, IntConditions(BoxRow.size), ColumnOrder(BoxRow.size))
    state = SearchableField(
        BoxRow.state, EnumConditions(BoxRow.state, BoxState), ColumnOrder(BoxRow.state)
    )
    spec_id = SearchableField(
        BoxRow.spec_id, UUIDConditions(BoxRow.spec_id), ColumnOrder(BoxRow.spec_id)
    )

    @override
    def to_data(self, row: BoxRow) -> BoxData:
        return BoxData(
            id=self.id.read(row),
            shelf_id=self.shelf_id.read(row),
            label=self.label.read(row),
            size=self.size.read(row),
            state=self.state.read(row),
            spec_id=self.spec_id.read(row),
        )


class _BoxNestedFields:
    """The box's own related rows: one spec, many items."""

    spec = NestedSearchableField(
        SpecSearchableFields.own,
        ToOneCorrelation(SpecRow, BoxRow, SpecRow.id == BoxRow.spec_id),
    )
    items = NestedSearchableField(
        ShelfItemSearchableFields.own,
        ToManyCorrelation(ShelfItemRow, BoxRow, ShelfItemRow.box_id == BoxRow.id),
    )


class BoxSearchableFields:
    own = _BoxOwnFields()
    nested = _BoxNestedFields


class _ShelfOwnFields(RowDataConverter[ShelfRow, ShelfData]):
    """The shelf's own columns."""

    id = SearchableField(ShelfRow.id, UUIDConditions(ShelfRow.id), ColumnOrder(ShelfRow.id))
    name = SearchableField(
        ShelfRow.name, StringConditions(ShelfRow.name), ColumnOrder(ShelfRow.name)
    )
    note = SearchableField(
        ShelfRow.note, StringConditions(ShelfRow.note), ColumnOrder(ShelfRow.note)
    )
    count = SearchableField(
        ShelfRow.count, IntConditions(ShelfRow.count), ColumnOrder(ShelfRow.count)
    )
    price = SearchableField(
        ShelfRow.price, DecimalConditions(ShelfRow.price), ColumnOrder(ShelfRow.price)
    )
    kind = SearchableField(
        ShelfRow.kind, EnumConditions(ShelfRow.kind, ShelfKind), ColumnOrder(ShelfRow.kind)
    )
    active = SearchableField(
        ShelfRow.active, BoolConditions(ShelfRow.active), ColumnOrder(ShelfRow.active)
    )
    tags = SearchableField(ShelfRow.tags, ArrayConditions(ShelfRow.tags, sa.String()), None)
    opened_at = SearchableField(
        ShelfRow.opened_at,
        DateTimeConditions(ShelfRow.opened_at),
        ColumnOrder(ShelfRow.opened_at),
    )
    closed_at = SearchableField(
        ShelfRow.closed_at,
        DateTimeConditions(ShelfRow.closed_at),
        ColumnOrder(ShelfRow.closed_at),
    )
    zone_id = SearchableField(
        ShelfRow.zone_id, UUIDConditions(ShelfRow.zone_id), ColumnOrder(ShelfRow.zone_id)
    )
    category_id = SearchableField(
        ShelfRow.category_id,
        UUIDConditions(ShelfRow.category_id),
        ColumnOrder(ShelfRow.category_id),
    )

    @override
    def to_data(self, row: ShelfRow) -> ShelfData:
        return ShelfData(
            id=self.id.read(row),
            name=self.name.read(row),
            note=self.note.read(row),
            count=self.count.read(row),
            price=self.price.read(row),
            kind=self.kind.read(row),
            active=self.active.read(row),
            tags=self.tags.read(row),
            opened_at=self.opened_at.read(row),
            closed_at=self.closed_at.read(row),
            zone_id=self.zone_id.read(row),
            category_id=self.category_id.read(row),
        )


class _ShelfNestedFields:
    """Rows of other tables a shelf reaches: many boxes, one category."""

    boxes = NestedSearchableField(
        BoxSearchableFields.own,
        ToManyCorrelation(BoxRow, ShelfRow, BoxRow.shelf_id == ShelfRow.id),
    )
    category = NestedSearchableField(
        CategorySearchableFields.own,
        ToOneCorrelation(CategoryRow, ShelfRow, CategoryRow.id == ShelfRow.category_id),
    )


class _ShelfLinkedEntities:
    """How a shelf connects to another entity; a revoked line is not a use."""

    carts = UsageConditions[CartID](
        ToManyCorrelation(
            CartLineRow,
            ShelfRow,
            sa.and_(
                CartLineRow.shelf_id == ShelfRow.id,
                CartLineRow.revoked.is_(False),
            ),
        ),
        CartLineRow.cart_id,
    )


class ShelfSearchableFields:
    own = _ShelfOwnFields()
    nested = _ShelfNestedFields
    linked = _ShelfLinkedEntities


@dataclass
class ShelfSearcher(Searcher[ShelfRow, ShelfData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ShelfRow)

    @override
    def to_data(self, row: ShelfRow) -> ShelfData:
        return ShelfSearchableFields.own.to_data(row)


class ZoneShelfTarget(ScopeTarget):
    """The shelves of one zone. The zone stands in for a real scope entity."""

    _zone_id: ZoneID

    def __init__(self, zone_id: ZoneID) -> None:
        self._zone_id = zone_id

    @override
    def scope_id(self) -> EntityIdentifier:
        return self._zone_id

    @override
    def to_condition(self) -> QueryCondition:
        zone_id = self._zone_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ShelfRow.zone_id == zone_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
