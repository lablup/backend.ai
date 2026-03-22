"""GraphQL tests for Fair Share resource weights with uses_default flag.

These tests verify that resource weight entries are correctly converted to
GraphQL types with the uses_default flag properly set.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from ai.backend.common.dto.manager.v2.fair_share.response import (
    DomainFairShareNode,
    ProjectFairShareNode,
    UserFairShareNode,
)
from ai.backend.common.dto.manager.v2.fair_share.types import (
    FairShareCalculationSnapshotInfo,
    FairShareSpecInfo,
    ResourceSlotInfo,
    ResourceWeightEntryInfo,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.adapters.fair_share import FairShareAdapter
from ai.backend.manager.api.gql.fair_share.types.common import (
    FairShareSpecGQL,
    ResourceWeightEntryGQL,
)
from ai.backend.manager.api.gql.fair_share.types.domain import DomainFairShareGQL
from ai.backend.manager.api.gql.fair_share.types.project import ProjectFairShareGQL
from ai.backend.manager.api.gql.fair_share.types.user import UserFairShareGQL
from ai.backend.manager.data.fair_share import (
    FairShareSpec,
)


class TestFairShareSpecGQLConversion:
    """Test FairShareSpecGQL.from_spec() conversion with resource weight entries."""

    def test_from_spec_with_mixed_defaults(self) -> None:
        """Scenario 3.1: Convert FairShareSpec to GQL with mixed default flags."""
        # Given
        spec = FairShareSpec(
            weight=Decimal("1.5"),
            half_life_days=7,
            lookback_days=28,
            decay_unit_days=1,
            resource_weights=ResourceSlot({
                "cpu": Decimal("1.0"),
                "mem": Decimal("0.001"),
                "cuda.device": Decimal("5.0"),
            }),
        )
        use_default = False
        uses_default_resources = frozenset(["cpu", "mem"])

        # When
        spec_info = FairShareAdapter._convert_spec(spec, use_default, uses_default_resources)
        gql_spec = FairShareSpecGQL.from_pydantic(spec_info)

        # Then
        assert gql_spec.weight == Decimal("1.5")
        assert gql_spec.uses_default is False
        assert len(gql_spec.resource_weights) == 3

        # Check each resource weight entry
        weight_dict = {entry.resource_type: entry for entry in gql_spec.resource_weights}

        # cpu uses default
        assert weight_dict["cpu"].weight == Decimal("1.0")
        assert weight_dict["cpu"].uses_default is True

        # mem uses default
        assert weight_dict["mem"].weight == Decimal("0.001")
        assert weight_dict["mem"].uses_default is True

        # cuda.device is explicit
        assert weight_dict["cuda.device"].weight == Decimal("5.0")
        assert weight_dict["cuda.device"].uses_default is False

    def test_from_spec_all_explicit(self) -> None:
        """Test conversion when all resource weights are explicit."""
        # Given
        spec = FairShareSpec(
            weight=Decimal("2.0"),
            half_life_days=7,
            lookback_days=28,
            decay_unit_days=1,
            resource_weights=ResourceSlot({
                "cpu": Decimal("2.0"),
                "mem": Decimal("0.5"),
            }),
        )
        use_default = False
        uses_default_resources: frozenset[str] = frozenset()  # Empty - all explicit

        # When
        spec_info = FairShareAdapter._convert_spec(spec, use_default, uses_default_resources)
        gql_spec = FairShareSpecGQL.from_pydantic(spec_info)

        # Then
        assert len(gql_spec.resource_weights) == 2
        for entry in gql_spec.resource_weights:
            assert entry.uses_default is False

    def test_from_spec_all_defaults(self) -> None:
        """Test conversion when all resource weights use defaults."""
        # Given
        spec = FairShareSpec(
            weight=Decimal("1.0"),
            half_life_days=7,
            lookback_days=28,
            decay_unit_days=1,
            resource_weights=ResourceSlot({
                "cpu": Decimal("1.0"),
                "mem": Decimal("0.001"),
            }),
        )
        use_default = True
        uses_default_resources = frozenset(["cpu", "mem"])

        # When
        spec_info = FairShareAdapter._convert_spec(spec, use_default, uses_default_resources)
        gql_spec = FairShareSpecGQL.from_pydantic(spec_info)

        # Then
        assert gql_spec.uses_default is True
        assert len(gql_spec.resource_weights) == 2
        for entry in gql_spec.resource_weights:
            assert entry.uses_default is True


class TestDomainFairShareGQLConversion:
    """Test DomainFairShareGQL.from_pydantic() with resource weight entries."""

    def test_from_pydantic_with_partial_defaults(self) -> None:
        """Scenario 3.2: Convert DomainFairShareNode to GQL."""
        # Given
        now = datetime.now(UTC)
        dto = DomainFairShareNode(
            id=str(uuid.uuid4()),
            resource_group_name="default",
            domain_name="test-domain",
            spec=FairShareSpecInfo(
                weight=Decimal("1.0"),
                uses_default=True,
                half_life_days=7,
                lookback_days=28,
                decay_unit_days=1,
                resource_weights=[
                    ResourceWeightEntryInfo(
                        resource_type="cpu", weight=Decimal("1.0"), uses_default=True
                    ),
                    ResourceWeightEntryInfo(
                        resource_type="mem", weight=Decimal("0.001"), uses_default=True
                    ),
                    ResourceWeightEntryInfo(
                        resource_type="cuda.device", weight=Decimal("10.0"), uses_default=False
                    ),
                ],
            ),
            calculation_snapshot=FairShareCalculationSnapshotInfo(
                fair_share_factor=Decimal("1.0"),
                total_decayed_usage=ResourceSlotInfo(entries=[]),
                normalized_usage=Decimal("0.0"),
                lookback_start=datetime.now(UTC).date(),
                lookback_end=datetime.now(UTC).date(),
                last_calculated_at=now,
            ),
            created_at=now,
            updated_at=now,
        )

        # When
        gql = DomainFairShareGQL.from_pydantic(dto)

        # Then
        assert gql.resource_group_name == "default"
        assert gql.domain_name == "test-domain"
        assert gql.spec.uses_default is True

        # Check resource weights
        weight_dict = {entry.resource_type: entry for entry in gql.spec.resource_weights}
        assert weight_dict["cpu"].uses_default is True
        assert weight_dict["mem"].uses_default is True
        assert weight_dict["cuda.device"].uses_default is False
        assert weight_dict["cuda.device"].weight == Decimal("10.0")


class TestProjectFairShareGQLConversion:
    """Test ProjectFairShareGQL.from_pydantic() with resource weight entries."""

    def test_from_pydantic(self) -> None:
        """Test Project fair share GQL conversion."""
        # Given
        now = datetime.now(UTC)
        project_id = uuid.uuid4()
        dto = ProjectFairShareNode(
            id=str(uuid.uuid4()),
            resource_group_name="default",
            project_id=project_id,
            domain_name="test-domain",
            spec=FairShareSpecInfo(
                weight=Decimal("1.5"),
                uses_default=False,
                half_life_days=7,
                lookback_days=28,
                decay_unit_days=1,
                resource_weights=[
                    ResourceWeightEntryInfo(
                        resource_type="cpu", weight=Decimal("1.0"), uses_default=True
                    ),
                    ResourceWeightEntryInfo(
                        resource_type="cuda.shares", weight=Decimal("0.1"), uses_default=False
                    ),
                ],
            ),
            calculation_snapshot=FairShareCalculationSnapshotInfo(
                fair_share_factor=Decimal("1.0"),
                total_decayed_usage=ResourceSlotInfo(entries=[]),
                normalized_usage=Decimal("0.0"),
                lookback_start=datetime.now(UTC).date(),
                lookback_end=datetime.now(UTC).date(),
                last_calculated_at=now,
            ),
            created_at=now,
            updated_at=now,
        )

        # When
        gql = ProjectFairShareGQL.from_pydantic(dto)

        # Then
        assert gql.project_id == project_id
        assert gql.spec.uses_default is False

        weight_dict = {entry.resource_type: entry for entry in gql.spec.resource_weights}
        assert weight_dict["cpu"].uses_default is True
        assert weight_dict["cuda.shares"].uses_default is False


class TestUserFairShareGQLConversion:
    """Test UserFairShareGQL.from_pydantic() with resource weight entries."""

    def test_from_pydantic(self) -> None:
        """Test User fair share GQL conversion."""
        # Given
        now = datetime.now(UTC)
        user_uuid = uuid.uuid4()
        project_id = uuid.uuid4()
        dto = UserFairShareNode(
            id=str(uuid.uuid4()),
            resource_group_name="default",
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="test-domain",
            spec=FairShareSpecInfo(
                weight=Decimal("1.0"),
                uses_default=True,
                half_life_days=7,
                lookback_days=28,
                decay_unit_days=1,
                resource_weights=[
                    ResourceWeightEntryInfo(
                        resource_type="cpu", weight=Decimal("1.0"), uses_default=True
                    ),
                    ResourceWeightEntryInfo(
                        resource_type="mem", weight=Decimal("0.001"), uses_default=True
                    ),
                ],
            ),
            calculation_snapshot=FairShareCalculationSnapshotInfo(
                fair_share_factor=Decimal("1.0"),
                total_decayed_usage=ResourceSlotInfo(entries=[]),
                normalized_usage=Decimal("0.0"),
                lookback_start=datetime.now(UTC).date(),
                lookback_end=datetime.now(UTC).date(),
                last_calculated_at=now,
            ),
            created_at=now,
            updated_at=now,
        )

        # When
        gql = UserFairShareGQL.from_pydantic(dto)

        # Then
        assert gql.user_uuid == user_uuid
        assert gql.project_id == project_id
        assert gql.spec.uses_default is True

        # All resources use defaults
        for entry in gql.spec.resource_weights:
            assert entry.uses_default is True


class TestResourceWeightEntryGQL:
    """Test ResourceWeightEntryGQL type."""

    def test_create_resource_weight_entry(self) -> None:
        """Test creating ResourceWeightEntryGQL instances."""
        # Given & When
        entry = ResourceWeightEntryGQL(
            resource_type="cuda.device", weight=Decimal("5.0"), uses_default=False
        )

        # Then
        assert entry.resource_type == "cuda.device"
        assert entry.weight == Decimal("5.0")
        assert entry.uses_default is False

    def test_decimal_precision_preserved(self) -> None:
        """Edge Case E.3: Verify Decimal precision is preserved."""
        # Given & When
        entry = ResourceWeightEntryGQL(
            resource_type="mem", weight=Decimal("0.001"), uses_default=True
        )

        # Then
        assert entry.weight == Decimal("0.001")
        assert str(entry.weight) == "0.001"
