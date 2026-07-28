"""Unit tests for the replica-group scheduling-history GraphQL input conversions.

The GQL layer is a thin wrapper over the v2 DTOs, so what matters here is that
every input reaches the adapter as the DTO it claims to be: the scope keeps its
non-empty guarantee, the category/order enums survive without value drift, and
the logical operators nest.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    ReplicaGroupHistoryFilter as ReplicaGroupHistoryFilterDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    ReplicaGroupHistoryOrder as ReplicaGroupHistoryOrderDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    OrderDirection,
    ReplicaGroupHistoryCategoryType,
    ReplicaGroupHistoryOrderField,
    ReplicaGroupHistoryScopeDTO,
)
from ai.backend.manager.api.gql.base import StringFilter
from ai.backend.manager.api.gql.rbac.types.scope import UUIDScopeGQL
from ai.backend.manager.api.gql.scheduling_history.types import (
    ReplicaGroupHistoryFilterGQL,
    ReplicaGroupHistoryOrderByGQL,
    ReplicaGroupHistoryScopeGQL,
)


@dataclass(frozen=True)
class _EmptyScopeCase:
    """A scope input that carries no target and must therefore be rejected."""

    label: str
    deployment: list[UUIDScopeGQL] | None


@pytest.fixture
def deployment_id() -> uuid.UUID:
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


class TestReplicaGroupHistoryScopeGQL:
    """Tests for ``ReplicaGroupHistoryScopeGQL.to_pydantic()``."""

    def test_deployment_scope_survives_conversion(self, deployment_id: uuid.UUID) -> None:
        scope = ReplicaGroupHistoryScopeGQL(deployment=[UUIDScopeGQL(value=deployment_id)])
        dto = scope.to_pydantic()
        assert isinstance(dto, ReplicaGroupHistoryScopeDTO)
        assert dto.deployment is not None
        assert [item.value for item in dto.deployment] == [deployment_id]

    @pytest.mark.parametrize(
        "case",
        [
            _EmptyScopeCase(label="omitted", deployment=None),
            _EmptyScopeCase(label="empty_list", deployment=[]),
        ],
        ids=lambda case: case.label,
    )
    def test_empty_scope_is_rejected(self, case: _EmptyScopeCase) -> None:
        scope = ReplicaGroupHistoryScopeGQL(deployment=case.deployment)
        with pytest.raises(ValidationError):
            scope.to_pydantic()


class TestReplicaGroupHistoryFilterGQL:
    """Tests for ``ReplicaGroupHistoryFilterGQL.to_pydantic()``."""

    @pytest.mark.parametrize(
        "category",
        list(ReplicaGroupHistoryCategoryType),
        ids=lambda category: category.value,
    )
    def test_category_survives_conversion(self, category: ReplicaGroupHistoryCategoryType) -> None:
        f = ReplicaGroupHistoryFilterGQL(category=[category])
        dto = f.to_pydantic()
        assert isinstance(dto, ReplicaGroupHistoryFilterDTO)
        assert dto.category == [category]

    def test_and_produces_sub_filter_dto(self) -> None:
        f = ReplicaGroupHistoryFilterGQL(
            AND=[ReplicaGroupHistoryFilterGQL(phase=StringFilter(equals="scale_out"))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, ReplicaGroupHistoryFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 1
        assert dto.AND[0].phase is not None
        assert dto.AND[0].phase.equals == "scale_out"

    def test_or_produces_sub_filter_dtos(self) -> None:
        f = ReplicaGroupHistoryFilterGQL(
            OR=[
                ReplicaGroupHistoryFilterGQL(phase=StringFilter(equals="scale_out")),
                ReplicaGroupHistoryFilterGQL(phase=StringFilter(equals="scale_in")),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, ReplicaGroupHistoryFilterDTO)
        assert dto.OR is not None
        assert [sub.phase.equals for sub in dto.OR if sub.phase is not None] == [
            "scale_out",
            "scale_in",
        ]

    def test_not_produces_sub_filter_dto(self) -> None:
        f = ReplicaGroupHistoryFilterGQL(
            NOT=[ReplicaGroupHistoryFilterGQL(error_code=StringFilter(equals="TIMEOUT"))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, ReplicaGroupHistoryFilterDTO)
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].error_code is not None
        assert dto.NOT[0].error_code.equals == "TIMEOUT"


class TestReplicaGroupHistoryOrderByGQL:
    """Tests for ``ReplicaGroupHistoryOrderByGQL.to_pydantic()``."""

    @pytest.mark.parametrize(
        "field",
        list(ReplicaGroupHistoryOrderField),
        ids=lambda field: field.value,
    )
    @pytest.mark.parametrize(
        "direction",
        list(OrderDirection),
        ids=lambda direction: direction.value,
    )
    def test_order_survives_conversion(
        self, field: ReplicaGroupHistoryOrderField, direction: OrderDirection
    ) -> None:
        order = ReplicaGroupHistoryOrderByGQL(field=field, direction=direction)
        dto = order.to_pydantic()
        assert isinstance(dto, ReplicaGroupHistoryOrderDTO)
        assert dto.field == field
        assert dto.direction == direction
