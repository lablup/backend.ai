"""Unit tests for the replica-group scheduling-history GraphQL input conversions.

The GQL layer is a thin wrapper over the v2 DTOs, so what matters here is that
every input reaches the adapter as the DTO it claims to be: the scope keeps its
non-empty guarantee, the category/order enums survive without value drift, and
the logical operators nest.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    ReplicaGroupHistoryFilter as ReplicaGroupHistoryFilterDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    ReplicaGroupHistoryOrder as ReplicaGroupHistoryOrderDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.response import (
    ReplicaGroupHistoryNode as ReplicaGroupHistoryNodeDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    OrderDirection as OrderDirectionDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    ReplicaGroupHistoryCategoryType,
    ReplicaGroupHistoryOrderField,
    ReplicaGroupHistoryScopeDTO,
)
from ai.backend.manager.api.gql.base import OrderDirection as OrderDirectionGQL
from ai.backend.manager.api.gql.base import StringFilter, UUIDFilter
from ai.backend.manager.api.gql.rbac.types.scope import UUIDScopeGQL
from ai.backend.manager.api.gql.scheduling_history.types import (
    ReplicaGroupHistoryCategoryGQL,
    ReplicaGroupHistoryFilterGQL,
    ReplicaGroupHistoryGQL,
    ReplicaGroupHistoryOrderByGQL,
    ReplicaGroupHistoryOrderFieldGQL,
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


@dataclass(frozen=True)
class _EnumPairCase:
    """A GQL enum and the DTO enum it must stay value-identical to."""

    label: str
    gql_enum: type[StrEnum]
    dto_enum: type[StrEnum]


class TestEnumParity:
    """The GQL enums restate the DTO enum values, so guard them against drift."""

    @pytest.mark.parametrize(
        "case",
        [
            _EnumPairCase(
                label="category",
                gql_enum=ReplicaGroupHistoryCategoryGQL,
                dto_enum=ReplicaGroupHistoryCategoryType,
            ),
            _EnumPairCase(
                label="order_field",
                gql_enum=ReplicaGroupHistoryOrderFieldGQL,
                dto_enum=ReplicaGroupHistoryOrderField,
            ),
        ],
        ids=lambda case: case.label,
    )
    def test_gql_enum_matches_dto_enum(self, case: _EnumPairCase) -> None:
        assert {member.name: member.value for member in case.gql_enum} == {
            member.name: member.value for member in case.dto_enum
        }


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


class TestReplicaGroupIsNotAddressable:
    """A replica group is internal, so its ID reaches no client-facing surface."""

    def test_gql_surfaces_carry_no_replica_group_id(self) -> None:
        assert not hasattr(ReplicaGroupHistoryGQL, "replica_group_id")
        assert not hasattr(ReplicaGroupHistoryFilterGQL, "replica_group_id")

    def test_dto_surfaces_carry_no_replica_group_id(self) -> None:
        assert "replica_group_id" not in ReplicaGroupHistoryNodeDTO.model_fields
        assert "replica_group_id" not in ReplicaGroupHistoryFilterDTO.model_fields

    def test_history_rows_are_not_refetchable_by_id(self) -> None:
        # Reachable only through the owning deployment, so there is no node(id:) path.
        assert "resolve_nodes" not in vars(ReplicaGroupHistoryGQL)


class TestReplicaGroupHistoryFilterGQL:
    """Tests for ``ReplicaGroupHistoryFilterGQL.to_pydantic()``."""

    def test_deployment_id_survives_conversion(self, deployment_id: uuid.UUID) -> None:
        f = ReplicaGroupHistoryFilterGQL(deployment_id=UUIDFilter(equals=deployment_id))
        dto = f.to_pydantic()
        assert isinstance(dto, ReplicaGroupHistoryFilterDTO)
        assert dto.deployment_id is not None
        assert dto.deployment_id.equals == deployment_id

    @pytest.mark.parametrize(
        "category",
        list(ReplicaGroupHistoryCategoryGQL),
        ids=lambda category: category.value,
    )
    def test_category_survives_conversion(self, category: ReplicaGroupHistoryCategoryGQL) -> None:
        f = ReplicaGroupHistoryFilterGQL(category=[category])
        dto = f.to_pydantic()
        assert isinstance(dto, ReplicaGroupHistoryFilterDTO)
        assert dto.category == [ReplicaGroupHistoryCategoryType(category.value)]

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
        list(ReplicaGroupHistoryOrderFieldGQL),
        ids=lambda field: field.value,
    )
    @pytest.mark.parametrize(
        "direction",
        list(OrderDirectionGQL),
        ids=lambda direction: direction.value,
    )
    def test_order_survives_conversion(
        self, field: ReplicaGroupHistoryOrderFieldGQL, direction: OrderDirectionGQL
    ) -> None:
        order = ReplicaGroupHistoryOrderByGQL(field=field, direction=direction)
        dto = order.to_pydantic()
        assert isinstance(dto, ReplicaGroupHistoryOrderDTO)
        assert dto.field == ReplicaGroupHistoryOrderField(field.value)
        assert dto.direction == OrderDirectionDTO(direction.value)
