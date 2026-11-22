"""Tests for the compute cluster GQL filter: the AND/OR/NOT combinators and the status
filter."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.compute_cluster.request import (
    ComputeClusterFilter as ComputeClusterFilterDTO,
)
from ai.backend.common.dto.manager.v2.compute_cluster.types import ComputeClusterStatus
from ai.backend.manager.api.gql.base import StringFilter
from ai.backend.manager.api.gql.compute_cluster.types import (
    ComputeClusterFilterGQL,
    ComputeClusterStatusFilterGQL,
    ComputeClusterStatusGQL,
)


class TestComputeClusterFilterCombinators:
    def test_empty(self) -> None:
        dto = ComputeClusterFilterGQL().to_pydantic()
        assert isinstance(dto, ComputeClusterFilterDTO)
        assert dto.AND is None and dto.OR is None and dto.NOT is None

    def test_and(self) -> None:
        f = ComputeClusterFilterGQL(
            AND=[
                ComputeClusterFilterGQL(name=StringFilter(contains="a")),
                ComputeClusterFilterGQL(name=StringFilter(contains="b")),
            ]
        )
        dto = f.to_pydantic()
        assert dto.AND is not None
        assert len(dto.AND) == 2
        assert dto.AND[0].name is not None
        assert dto.AND[0].name.contains == "a"

    def test_or(self) -> None:
        f = ComputeClusterFilterGQL(OR=[ComputeClusterFilterGQL(name=StringFilter(contains="a"))])
        dto = f.to_pydantic()
        assert dto.OR is not None
        assert len(dto.OR) == 1

    def test_not(self) -> None:
        f = ComputeClusterFilterGQL(NOT=[ComputeClusterFilterGQL(name=StringFilter(equals="x"))])
        dto = f.to_pydantic()
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].name is not None
        assert dto.NOT[0].name.equals == "x"


class TestComputeClusterStatusFilter:
    def test_status_values_reach_the_dto_enum(self) -> None:
        f = ComputeClusterFilterGQL(
            status=ComputeClusterStatusFilterGQL(
                equals=ComputeClusterStatusGQL.ALIVE,
                not_in=[ComputeClusterStatusGQL.LOST],
            )
        )
        dto = f.to_pydantic()
        assert dto.status is not None
        assert dto.status.equals == ComputeClusterStatus.ALIVE
        assert dto.status.not_in == [ComputeClusterStatus.LOST]
