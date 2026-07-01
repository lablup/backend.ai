"""Tests for the AND/OR/NOT combinators on the login client type GQL filter."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.login_client_type.request import (
    LoginClientTypeFilter as LoginClientTypeFilterDTO,
)
from ai.backend.manager.api.gql.base import StringFilter
from ai.backend.manager.api.gql.login_client_type.types import LoginClientTypeFilterGQL


class TestLoginClientTypeFilterCombinators:
    """Tests for AND/OR/NOT combinators on LoginClientTypeFilterGQL."""

    def test_empty(self) -> None:
        dto = LoginClientTypeFilterGQL().to_pydantic()
        assert isinstance(dto, LoginClientTypeFilterDTO)
        assert dto.AND is None and dto.OR is None and dto.NOT is None

    def test_and(self) -> None:
        f = LoginClientTypeFilterGQL(
            AND=[
                LoginClientTypeFilterGQL(name=StringFilter(contains="a")),
                LoginClientTypeFilterGQL(name=StringFilter(contains="b")),
            ]
        )
        dto = f.to_pydantic()
        assert dto.AND is not None
        assert len(dto.AND) == 2
        assert dto.AND[0].name is not None
        assert dto.AND[0].name.contains == "a"

    def test_or(self) -> None:
        f = LoginClientTypeFilterGQL(OR=[LoginClientTypeFilterGQL(name=StringFilter(contains="a"))])
        dto = f.to_pydantic()
        assert dto.OR is not None
        assert len(dto.OR) == 1

    def test_not(self) -> None:
        f = LoginClientTypeFilterGQL(NOT=[LoginClientTypeFilterGQL(name=StringFilter(equals="x"))])
        dto = f.to_pydantic()
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].name is not None
        assert dto.NOT[0].name.equals == "x"
