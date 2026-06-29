"""Tests for the AND/OR/NOT combinators on container registry GQL filter types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.container_registry.request import (
    ContainerRegistryFilter as ContainerRegistryFilterDTO,
)
from ai.backend.manager.api.gql.base import StringFilter
from ai.backend.manager.api.gql.container_registry.filters import ContainerRegistryV2Filter


class TestContainerRegistryFilterCombinators:
    """Tests for AND/OR/NOT combinators on ContainerRegistryV2Filter."""

    def test_to_pydantic_empty(self) -> None:
        dto = ContainerRegistryV2Filter().to_pydantic()
        assert dto.AND is None
        assert dto.OR is None
        assert dto.NOT is None

    def test_to_pydantic_and(self) -> None:
        filter_gql = ContainerRegistryV2Filter(
            AND=[
                ContainerRegistryV2Filter(registry_name=StringFilter(contains="a")),
                ContainerRegistryV2Filter(registry_name=StringFilter(contains="b")),
            ]
        )
        dto = filter_gql.to_pydantic()
        assert isinstance(dto, ContainerRegistryFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 2
        assert dto.AND[0].registry_name is not None
        assert dto.AND[0].registry_name.contains == "a"

    def test_to_pydantic_or(self) -> None:
        filter_gql = ContainerRegistryV2Filter(
            OR=[
                ContainerRegistryV2Filter(registry_name=StringFilter(contains="a")),
                ContainerRegistryV2Filter(registry_name=StringFilter(contains="b")),
            ]
        )
        dto = filter_gql.to_pydantic()
        assert dto.OR is not None
        assert len(dto.OR) == 2

    def test_to_pydantic_not(self) -> None:
        filter_gql = ContainerRegistryV2Filter(
            NOT=[ContainerRegistryV2Filter(registry_name=StringFilter(equals="x"))]
        )
        dto = filter_gql.to_pydantic()
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].registry_name is not None
        assert dto.NOT[0].registry_name.equals == "x"
