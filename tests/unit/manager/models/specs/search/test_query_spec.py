from __future__ import annotations

from collections.abc import Callable

import pytest
import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import (
    NestedQueryColumn,
    QueryColumn,
    SearchableField,
)
from ai.backend.manager.models.specs.search.query_spec import (
    QueryAggregateSection,
    QueryLinkedSection,
    QueryNestedSection,
    QueryOwnSection,
    QuerySpec,
)

from .shelf_rows import BoxRow, ShelfRow

type Render = Callable[[sa.sql.ClauseElement], str]


class _BoxOwnColumns(QueryOwnSection):
    id = QueryColumn(BoxRow.id, UUIDConditions(BoxRow.id), ColumnOrder(BoxRow.id))
    label = QueryColumn(BoxRow.label, StringConditions(BoxRow.label), ColumnOrder(BoxRow.label))


class _ShelfOwnColumns(QueryOwnSection):
    id = QueryColumn(ShelfRow.id, UUIDConditions(ShelfRow.id), ColumnOrder(ShelfRow.id))
    name = QueryColumn(ShelfRow.name, StringConditions(ShelfRow.name), ColumnOrder(ShelfRow.name))
    count = QueryColumn(ShelfRow.count, IntConditions(ShelfRow.count), ColumnOrder(ShelfRow.count))
    tags = QueryColumn(ShelfRow.tags, None, None)


class _ShelfNestedColumns(QueryNestedSection):
    boxes = NestedQueryColumn(
        _BoxOwnColumns(),
        ToManyCorrelation(BoxRow, ShelfRow, BoxRow.shelf_id == ShelfRow.id),
    )


class _ShelfQuerySpec(QuerySpec):
    own = _ShelfOwnColumns()
    nested = _ShelfNestedColumns


class _OwnOnlyQuerySpec(QuerySpec):
    own = _BoxOwnColumns()


class _ShelfSearchableFields:
    name = SearchableField(
        ShelfRow.name, StringConditions(ShelfRow.name), ColumnOrder(ShelfRow.name)
    )


class TestQueryColumnName:
    def test_own_columns_are_named_after_their_attributes(self) -> None:
        columns = {
            attribute: value
            for attribute, value in vars(_ShelfOwnColumns).items()
            if isinstance(value, QueryColumn)
        }

        assert {attribute: column.name for attribute, column in columns.items()} == {
            "id": "id",
            "name": "name",
            "count": "count",
            "tags": "tags",
        }

    def test_name_follows_the_attribute_not_the_column(self) -> None:
        class _Columns(QueryOwnSection):
            title = QueryColumn(ShelfRow.name, None, None)

        assert _Columns.title.name == "title"

    def test_nested_section_columns_are_named(self) -> None:
        assert _ShelfQuerySpec.nested.boxes.columns.label.name == "label"


class TestQueryOwnSectionColumns:
    def test_columns_are_keyed_by_name_in_declaration_order(self) -> None:
        own = _ShelfQuerySpec.own
        assert list(own.columns().items()) == [
            ("id", own.id),
            ("name", own.name),
            ("count", own.count),
            ("tags", own.tags),
        ]

    def test_base_class_columns_come_first_and_searchable_fields_are_left_out(self) -> None:
        class _Columns(_BoxOwnColumns):
            title = QueryColumn(BoxRow.label, None, None)
            legacy = SearchableField(BoxRow.label, None, None)

        assert list(_Columns().columns()) == ["id", "label", "title"]


class TestQueryColumnSQL:
    def test_condition_matches_searchable_field(self, render: Render) -> None:
        spec = StringMatchSpec(value="a", case_insensitive=False, negated=False)
        from_column = _ShelfQuerySpec.own.name.filter.equals(spec)
        from_field = _ShelfSearchableFields.name.filter.equals(spec)

        assert render(sa.select(ShelfRow.id).where(from_column())) == render(
            sa.select(ShelfRow.id).where(from_field())
        )

    @pytest.mark.parametrize("ascending", [True, False])
    def test_order_matches_searchable_field(self, render: Render, ascending: bool) -> None:
        from_column = _ShelfQuerySpec.own.name.order.apply(ascending)
        from_field = _ShelfSearchableFields.name.order.apply(ascending)

        assert render(from_column) == render(from_field)

    def test_empty_slots_stay_none(self) -> None:
        assert _ShelfQuerySpec.own.tags.filter is None
        assert _ShelfQuerySpec.own.tags.order is None


class TestNestedQueryColumn:
    def test_holds_columns_and_correlation(self, render: Render) -> None:
        boxes = _ShelfQuerySpec.nested.boxes
        condition = boxes.correlation.some([
            boxes.columns.label.filter.equals(
                StringMatchSpec(value="a", case_insensitive=False, negated=False)
            )
        ])

        assert isinstance(boxes.columns, _BoxOwnColumns)
        assert render(sa.select(ShelfRow.id).where(condition())) == render(
            sa.select(ShelfRow.id).where(
                sa.exists(
                    sa.select(sa.literal(1))
                    .select_from(BoxRow)
                    .where(BoxRow.shelf_id == ShelfRow.id)
                    .where(BoxRow.label == "a")
                    .correlate(ShelfRow)
                )
            )
        )


class TestQuerySpecSections:
    def test_unset_sections_default_to_empty_bases(self) -> None:
        assert _OwnOnlyQuerySpec.nested is QueryNestedSection
        assert _OwnOnlyQuerySpec.linked is QueryLinkedSection
        assert _OwnOnlyQuerySpec.aggregate is QueryAggregateSection

    def test_declared_sections_are_kept(self) -> None:
        assert isinstance(_ShelfQuerySpec.own, _ShelfOwnColumns)
        assert _ShelfQuerySpec.nested is _ShelfNestedColumns
