"""Tests for AND/OR/NOT combinators on the RuntimeVariant GQL filter."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    RuntimeVariantFilter as RuntimeVariantFilterDTO,
)
from ai.backend.manager.api.gql.base import StringFilter as StringFilterGQL
from ai.backend.manager.api.gql.runtime_variant.types import RuntimeVariantFilterGQL


class TestRuntimeVariantFilterCombinators:
    """Tests for AND/OR/NOT combinators on RuntimeVariantFilterGQL."""

    def test_empty(self) -> None:
        dto = RuntimeVariantFilterGQL().to_pydantic()
        assert isinstance(dto, RuntimeVariantFilterDTO)
        assert dto.AND is None
        assert dto.OR is None
        assert dto.NOT is None

    def test_and(self) -> None:
        f = RuntimeVariantFilterGQL(
            AND=[
                RuntimeVariantFilterGQL(name=StringFilterGQL(contains="a")),
                RuntimeVariantFilterGQL(name=StringFilterGQL(contains="b")),
            ]
        )
        dto = f.to_pydantic()
        assert isinstance(dto, RuntimeVariantFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 2
        assert dto.AND[0].name is not None
        assert dto.AND[0].name.contains == "a"

    def test_or(self) -> None:
        f = RuntimeVariantFilterGQL(
            OR=[RuntimeVariantFilterGQL(name=StringFilterGQL(contains="a"))]
        )
        dto = f.to_pydantic()
        assert dto.OR is not None
        assert len(dto.OR) == 1

    def test_not(self) -> None:
        f = RuntimeVariantFilterGQL(NOT=[RuntimeVariantFilterGQL(name=StringFilterGQL(equals="x"))])
        dto = f.to_pydantic()
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].name is not None
        assert dto.NOT[0].name.equals == "x"
