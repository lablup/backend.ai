"""Tests for AND/OR/NOT combinators on the app config definition GQL filter."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    AppConfigDefinitionFilter as AppConfigDefinitionFilterDTO,
)
from ai.backend.manager.api.gql.app_config_definition.types import (
    AppConfigDefinitionFilterGQL,
)
from ai.backend.manager.api.gql.base import StringFilter


class TestAppConfigDefinitionFilterCombinators:
    """Tests for AND/OR/NOT combinators on AppConfigDefinitionFilterGQL."""

    def test_empty(self) -> None:
        dto = AppConfigDefinitionFilterGQL().to_pydantic()
        assert dto.AND is None
        assert dto.OR is None
        assert dto.NOT is None

    def test_and(self) -> None:
        f = AppConfigDefinitionFilterGQL(
            AND=[
                AppConfigDefinitionFilterGQL(config_name=StringFilter(contains="a")),
                AppConfigDefinitionFilterGQL(config_name=StringFilter(contains="b")),
            ]
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AppConfigDefinitionFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 2

    def test_or(self) -> None:
        f = AppConfigDefinitionFilterGQL(
            OR=[AppConfigDefinitionFilterGQL(config_name=StringFilter(contains="a"))]
        )
        dto = f.to_pydantic()
        assert dto.OR is not None
        assert len(dto.OR) == 1

    def test_not(self) -> None:
        f = AppConfigDefinitionFilterGQL(
            NOT=[AppConfigDefinitionFilterGQL(config_name=StringFilter(equals="x"))]
        )
        dto = f.to_pydantic()
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
