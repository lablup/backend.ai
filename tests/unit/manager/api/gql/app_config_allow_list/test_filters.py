"""Tests for AND/OR/NOT combinators on the app config allow-list GQL filter."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    AppConfigAllowListFilter as AppConfigAllowListFilterDTO,
)
from ai.backend.manager.api.gql.app_config_allow_list.types import (
    AppConfigAllowListFilterGQL,
)
from ai.backend.manager.api.gql.base import StringFilter


class TestAppConfigAllowListFilterCombinators:
    """Tests for AND/OR/NOT combinators on AppConfigAllowListFilterGQL."""

    def test_empty(self) -> None:
        dto = AppConfigAllowListFilterGQL().to_pydantic()
        assert dto.AND is None
        assert dto.OR is None
        assert dto.NOT is None

    def test_and(self) -> None:
        f = AppConfigAllowListFilterGQL(
            AND=[
                AppConfigAllowListFilterGQL(config_name=StringFilter(contains="a")),
                AppConfigAllowListFilterGQL(config_name=StringFilter(contains="b")),
            ]
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AppConfigAllowListFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 2

    def test_or(self) -> None:
        f = AppConfigAllowListFilterGQL(
            OR=[AppConfigAllowListFilterGQL(config_name=StringFilter(contains="a"))]
        )
        dto = f.to_pydantic()
        assert dto.OR is not None
        assert len(dto.OR) == 1

    def test_not(self) -> None:
        f = AppConfigAllowListFilterGQL(
            NOT=[AppConfigAllowListFilterGQL(config_name=StringFilter(equals="x"))]
        )
        dto = f.to_pydantic()
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
