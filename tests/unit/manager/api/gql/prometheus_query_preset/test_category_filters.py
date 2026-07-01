"""Tests for the AND/OR/NOT combinators on the query preset category GQL filter."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    CategoryFilter as CategoryFilterDTO,
)
from ai.backend.manager.api.gql.base import StringFilter
from ai.backend.manager.api.gql.prometheus_query_preset.types.category import CategoryFilterGQL


class TestCategoryFilterCombinators:
    """Tests for AND/OR/NOT combinators on CategoryFilterGQL."""

    def test_empty(self) -> None:
        dto = CategoryFilterGQL().to_pydantic()
        assert isinstance(dto, CategoryFilterDTO)
        assert dto.AND is None and dto.OR is None and dto.NOT is None

    def test_and(self) -> None:
        f = CategoryFilterGQL(
            AND=[
                CategoryFilterGQL(name=StringFilter(contains="a")),
                CategoryFilterGQL(name=StringFilter(contains="b")),
            ]
        )
        dto = f.to_pydantic()
        assert dto.AND is not None
        assert len(dto.AND) == 2
        assert dto.AND[0].name is not None
        assert dto.AND[0].name.contains == "a"

    def test_or(self) -> None:
        f = CategoryFilterGQL(OR=[CategoryFilterGQL(name=StringFilter(contains="a"))])
        dto = f.to_pydantic()
        assert dto.OR is not None
        assert len(dto.OR) == 1

    def test_not(self) -> None:
        f = CategoryFilterGQL(NOT=[CategoryFilterGQL(name=StringFilter(equals="x"))])
        dto = f.to_pydantic()
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].name is not None
        assert dto.NOT[0].name.equals == "x"
