"""Tests for ai.backend.common.dto.manager.v2.fair_share.types module."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal

from ai.backend.common.dto.manager.v2.fair_share.types import (
    DomainFairShareOrderField,
    DomainUsageBucketOrderField,
    FairShareCalculationSnapshotInfo,
    FairShareSpecInfo,
    OrderDirection,
    ProjectFairShareOrderField,
    ProjectUsageBucketOrderField,
    ResourceSlotEntryInfo,
    ResourceSlotInfo,
    UsageBucketMetadataInfo,
    UserFairShareOrderField,
    UserUsageBucketOrderField,
)


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_member_count(self) -> None:
        assert len(OrderDirection) == 2

    def test_is_str_enum(self) -> None:
        assert isinstance(OrderDirection.ASC, str)
        assert isinstance(OrderDirection.DESC, str)

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestDomainFairShareOrderField:
    """Tests for DomainFairShareOrderField enum."""

    def test_fair_share_factor_value(self) -> None:
        assert DomainFairShareOrderField.FAIR_SHARE_FACTOR.value == "fair_share_factor"

    def test_domain_name_value(self) -> None:
        assert DomainFairShareOrderField.DOMAIN_NAME.value == "domain_name"

    def test_created_at_value(self) -> None:
        assert DomainFairShareOrderField.CREATED_AT.value == "created_at"

    def test_member_count(self) -> None:
        assert len(DomainFairShareOrderField) == 3

    def test_from_string(self) -> None:
        assert (
            DomainFairShareOrderField("fair_share_factor")
            is DomainFairShareOrderField.FAIR_SHARE_FACTOR
        )


class TestProjectFairShareOrderField:
    """Tests for ProjectFairShareOrderField enum."""

    def test_fair_share_factor_value(self) -> None:
        assert ProjectFairShareOrderField.FAIR_SHARE_FACTOR.value == "fair_share_factor"

    def test_created_at_value(self) -> None:
        assert ProjectFairShareOrderField.CREATED_AT.value == "created_at"

    def test_member_count(self) -> None:
        assert len(ProjectFairShareOrderField) == 2


class TestUserFairShareOrderField:
    """Tests for UserFairShareOrderField enum."""

    def test_fair_share_factor_value(self) -> None:
        assert UserFairShareOrderField.FAIR_SHARE_FACTOR.value == "fair_share_factor"

    def test_created_at_value(self) -> None:
        assert UserFairShareOrderField.CREATED_AT.value == "created_at"

    def test_member_count(self) -> None:
        assert len(UserFairShareOrderField) == 2


class TestDomainUsageBucketOrderField:
    """Tests for DomainUsageBucketOrderField enum."""

    def test_period_start_value(self) -> None:
        assert DomainUsageBucketOrderField.PERIOD_START.value == "period_start"

    def test_member_count(self) -> None:
        assert len(DomainUsageBucketOrderField) == 1


class TestProjectUsageBucketOrderField:
    """Tests for ProjectUsageBucketOrderField enum."""

    def test_period_start_value(self) -> None:
        assert ProjectUsageBucketOrderField.PERIOD_START.value == "period_start"

    def test_member_count(self) -> None:
        assert len(ProjectUsageBucketOrderField) == 1


class TestUserUsageBucketOrderField:
    """Tests for UserUsageBucketOrderField enum."""

    def test_period_start_value(self) -> None:
        assert UserUsageBucketOrderField.PERIOD_START.value == "period_start"

    def test_member_count(self) -> None:
        assert len(UserUsageBucketOrderField) == 1


class TestResourceSlotEntryInfo:
    """Tests for ResourceSlotEntryInfo sub-model."""

    def test_creation_with_all_fields(self) -> None:
        entry = ResourceSlotEntryInfo(resource_type="cpu", quantity="4")
        assert entry.resource_type == "cpu"
        assert entry.quantity == "4"

    def test_cuda_resource_type(self) -> None:
        entry = ResourceSlotEntryInfo(resource_type="cuda.shares", quantity="2.5")
        assert entry.resource_type == "cuda.shares"
        assert entry.quantity == "2.5"

    def test_round_trip_serialization(self) -> None:
        entry = ResourceSlotEntryInfo(resource_type="mem", quantity="8192")
        json_str = entry.model_dump_json()
        restored = ResourceSlotEntryInfo.model_validate_json(json_str)
        assert restored.resource_type == "mem"
        assert restored.quantity == "8192"

    def test_model_dump_json(self) -> None:
        entry = ResourceSlotEntryInfo(resource_type="cpu", quantity="2")
        data = json.loads(entry.model_dump_json())
        assert data["resource_type"] == "cpu"
        assert data["quantity"] == "2"


class TestResourceSlotInfo:
    """Tests for ResourceSlotInfo sub-model."""

    def test_creation_with_empty_entries(self) -> None:
        info = ResourceSlotInfo(entries=[])
        assert info.entries == []

    def test_creation_with_entries(self) -> None:
        entries = [
            ResourceSlotEntryInfo(resource_type="cpu", quantity="4"),
            ResourceSlotEntryInfo(resource_type="mem", quantity="8192"),
        ]
        info = ResourceSlotInfo(entries=entries)
        assert len(info.entries) == 2
        assert info.entries[0].resource_type == "cpu"
        assert info.entries[1].resource_type == "mem"

    def test_round_trip_serialization(self) -> None:
        entries = [ResourceSlotEntryInfo(resource_type="cpu", quantity="4")]
        info = ResourceSlotInfo(entries=entries)
        json_str = info.model_dump_json()
        restored = ResourceSlotInfo.model_validate_json(json_str)
        assert len(restored.entries) == 1
        assert restored.entries[0].resource_type == "cpu"
        assert restored.entries[0].quantity == "4"


class TestFairShareSpecInfo:
    """Tests for FairShareSpecInfo sub-model."""

    def _make_resource_slot(self) -> ResourceSlotInfo:
        return ResourceSlotInfo(entries=[ResourceSlotEntryInfo(resource_type="cpu", quantity="1")])

    def test_creation_with_all_fields(self) -> None:
        spec = FairShareSpecInfo(
            weight=Decimal("1.5"),
            half_life_days=30,
            lookback_days=90,
            decay_unit_days=1,
            resource_weights=self._make_resource_slot(),
        )
        assert spec.weight == Decimal("1.5")
        assert spec.half_life_days == 30
        assert spec.lookback_days == 90
        assert spec.decay_unit_days == 1

    def test_weight_none_is_valid(self) -> None:
        spec = FairShareSpecInfo(
            weight=None,
            half_life_days=30,
            lookback_days=90,
            decay_unit_days=1,
            resource_weights=self._make_resource_slot(),
        )
        assert spec.weight is None

    def test_default_weight_is_none(self) -> None:
        spec = FairShareSpecInfo(
            half_life_days=30,
            lookback_days=90,
            decay_unit_days=1,
            resource_weights=self._make_resource_slot(),
        )
        assert spec.weight is None

    def test_nested_resource_weights(self) -> None:
        spec = FairShareSpecInfo(
            half_life_days=30,
            lookback_days=90,
            decay_unit_days=1,
            resource_weights=self._make_resource_slot(),
        )
        assert isinstance(spec.resource_weights, ResourceSlotInfo)
        assert len(spec.resource_weights.entries) == 1

    def test_round_trip_serialization(self) -> None:
        spec = FairShareSpecInfo(
            weight=Decimal("2.0"),
            half_life_days=14,
            lookback_days=60,
            decay_unit_days=1,
            resource_weights=self._make_resource_slot(),
        )
        json_str = spec.model_dump_json()
        restored = FairShareSpecInfo.model_validate_json(json_str)
        assert restored.weight == Decimal("2.0")
        assert restored.half_life_days == 14
        assert restored.lookback_days == 60


class TestFairShareCalculationSnapshotInfo:
    """Tests for FairShareCalculationSnapshotInfo sub-model."""

    def _make_resource_slot(self) -> ResourceSlotInfo:
        return ResourceSlotInfo(entries=[ResourceSlotEntryInfo(resource_type="cpu", quantity="4")])

    def test_creation_with_all_fields(self) -> None:
        snapshot = FairShareCalculationSnapshotInfo(
            fair_share_factor=Decimal("0.25"),
            total_decayed_usage=self._make_resource_slot(),
            normalized_usage=Decimal("100.5"),
            lookback_start=date(2025, 1, 1),
            lookback_end=date(2025, 3, 31),
            last_calculated_at=datetime(2025, 3, 31, 12, 0, 0, tzinfo=UTC),
        )
        assert snapshot.fair_share_factor == Decimal("0.25")
        assert snapshot.normalized_usage == Decimal("100.5")
        assert snapshot.lookback_start == date(2025, 1, 1)
        assert snapshot.lookback_end == date(2025, 3, 31)

    def test_nested_total_decayed_usage(self) -> None:
        snapshot = FairShareCalculationSnapshotInfo(
            fair_share_factor=Decimal("0.5"),
            total_decayed_usage=self._make_resource_slot(),
            normalized_usage=Decimal("50.0"),
            lookback_start=date(2025, 1, 1),
            lookback_end=date(2025, 3, 31),
            last_calculated_at=datetime(2025, 3, 31, 0, 0, 0, tzinfo=UTC),
        )
        assert isinstance(snapshot.total_decayed_usage, ResourceSlotInfo)
        assert snapshot.total_decayed_usage.entries[0].resource_type == "cpu"

    def test_round_trip_serialization(self) -> None:
        snapshot = FairShareCalculationSnapshotInfo(
            fair_share_factor=Decimal("0.1"),
            total_decayed_usage=self._make_resource_slot(),
            normalized_usage=Decimal("200.0"),
            lookback_start=date(2025, 2, 1),
            lookback_end=date(2025, 3, 1),
            last_calculated_at=datetime(2025, 3, 1, 0, 0, 0, tzinfo=UTC),
        )
        json_str = snapshot.model_dump_json()
        restored = FairShareCalculationSnapshotInfo.model_validate_json(json_str)
        assert restored.fair_share_factor == Decimal("0.1")
        assert restored.normalized_usage == Decimal("200.0")


class TestUsageBucketMetadataInfo:
    """Tests for UsageBucketMetadataInfo sub-model."""

    def _make_resource_slot(self) -> ResourceSlotInfo:
        return ResourceSlotInfo(
            entries=[ResourceSlotEntryInfo(resource_type="mem", quantity="2048")]
        )

    def test_creation_with_all_fields(self) -> None:
        now = datetime(2025, 3, 17, 0, 0, 0, tzinfo=UTC)
        meta = UsageBucketMetadataInfo(
            period_start=date(2025, 3, 16),
            period_end=date(2025, 3, 17),
            decay_unit_days=1,
            created_at=now,
            updated_at=now,
            average_daily_usage=self._make_resource_slot(),
            usage_capacity_ratio=self._make_resource_slot(),
        )
        assert meta.period_start == date(2025, 3, 16)
        assert meta.period_end == date(2025, 3, 17)
        assert meta.decay_unit_days == 1

    def test_nested_average_daily_usage(self) -> None:
        now = datetime(2025, 3, 17, 0, 0, 0, tzinfo=UTC)
        meta = UsageBucketMetadataInfo(
            period_start=date(2025, 3, 16),
            period_end=date(2025, 3, 17),
            decay_unit_days=1,
            created_at=now,
            updated_at=now,
            average_daily_usage=self._make_resource_slot(),
            usage_capacity_ratio=self._make_resource_slot(),
        )
        assert isinstance(meta.average_daily_usage, ResourceSlotInfo)
        assert isinstance(meta.usage_capacity_ratio, ResourceSlotInfo)

    def test_round_trip_serialization(self) -> None:
        now = datetime(2025, 3, 17, 0, 0, 0, tzinfo=UTC)
        meta = UsageBucketMetadataInfo(
            period_start=date(2025, 3, 1),
            period_end=date(2025, 3, 2),
            decay_unit_days=1,
            created_at=now,
            updated_at=now,
            average_daily_usage=self._make_resource_slot(),
            usage_capacity_ratio=self._make_resource_slot(),
        )
        json_str = meta.model_dump_json()
        restored = UsageBucketMetadataInfo.model_validate_json(json_str)
        assert restored.period_start == date(2025, 3, 1)
        assert restored.period_end == date(2025, 3, 2)
        assert restored.decay_unit_days == 1
