"""Tests for AND/OR/NOT combinators on the RuntimeVariantPreset GQL filter."""

from __future__ import annotations

import uuid

from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    RuntimeVariantPresetFilter as RuntimeVariantPresetFilterDTO,
)
from ai.backend.manager.api.gql.base import StringFilter as StringFilterGQL
from ai.backend.manager.api.gql.base import UUIDFilter as UUIDFilterGQL
from ai.backend.manager.api.gql.runtime_variant_preset.types import RuntimeVariantPresetFilterGQL


class TestRuntimeVariantPresetFilterCombinators:
    """Tests for AND/OR/NOT combinators on RuntimeVariantPresetFilterGQL."""

    def test_empty(self) -> None:
        dto = RuntimeVariantPresetFilterGQL().to_pydantic()
        assert isinstance(dto, RuntimeVariantPresetFilterDTO)
        assert dto.AND is None
        assert dto.OR is None
        assert dto.NOT is None

    def test_and(self) -> None:
        f = RuntimeVariantPresetFilterGQL(
            AND=[
                RuntimeVariantPresetFilterGQL(name=StringFilterGQL(contains="a")),
                RuntimeVariantPresetFilterGQL(name=StringFilterGQL(contains="b")),
            ]
        )
        dto = f.to_pydantic()
        assert isinstance(dto, RuntimeVariantPresetFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 2
        assert dto.AND[0].name is not None
        assert dto.AND[0].name.contains == "a"

    def test_or(self) -> None:
        variant_id = uuid.uuid4()
        f = RuntimeVariantPresetFilterGQL(
            OR=[RuntimeVariantPresetFilterGQL(runtime_variant_id=UUIDFilterGQL(equals=variant_id))]
        )
        dto = f.to_pydantic()
        assert dto.OR is not None
        assert len(dto.OR) == 1
        assert dto.OR[0].runtime_variant_id is not None
        assert dto.OR[0].runtime_variant_id.equals == variant_id

    def test_not(self) -> None:
        f = RuntimeVariantPresetFilterGQL(
            NOT=[RuntimeVariantPresetFilterGQL(name=StringFilterGQL(equals="x"))]
        )
        dto = f.to_pydantic()
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].name is not None
        assert dto.NOT[0].name.equals == "x"
