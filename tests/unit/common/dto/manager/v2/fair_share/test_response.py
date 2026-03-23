"""Tests for ai.backend.common.dto.manager.v2.fair_share.response module."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertDomainFairShareWeightPayload,
    BulkUpsertProjectFairShareWeightPayload,
    BulkUpsertUserFairShareWeightPayload,
    DomainFairShareNode,
    DomainUsageBucketNode,
    GetDomainFairSharePayload,
    GetProjectFairSharePayload,
    GetResourceGroupFairShareSpecPayload,
    GetUserFairSharePayload,
    ProjectFairShareNode,
    ProjectUsageBucketNode,
    ResourceGroupFairShareSpecNode,
    SearchDomainFairSharesPayload,
    SearchDomainUsageBucketsPayload,
    SearchProjectFairSharesPayload,
    SearchProjectUsageBucketsPayload,
    SearchUserFairSharesPayload,
    SearchUserUsageBucketsPayload,
    UpdateResourceGroupFairShareSpecPayload,
    UpsertDomainFairShareWeightPayload,
    UpsertProjectFairShareWeightPayload,
    UpsertUserFairShareWeightPayload,
    UserFairShareNode,
    UserUsageBucketNode,
)
from ai.backend.common.dto.manager.v2.fair_share.types import (
    FairShareCalculationSnapshotInfo,
    FairShareSpecInfo,
    ResourceSlotEntryInfo,
    ResourceSlotInfo,
    ResourceWeightEntryInfo,
    UsageBucketMetadataInfo,
)

_UUID1 = UUID("550e8400-e29b-41d4-a716-446655440000")
_UUID2 = UUID("660e8400-e29b-41d4-a716-446655440001")
_UUID3 = UUID("770e8400-e29b-41d4-a716-446655440002")
_NOW = datetime(2025, 3, 17, 12, 0, 0, tzinfo=UTC)
_DATE_START = date(2025, 1, 1)
_DATE_END = date(2025, 3, 31)


def _make_resource_slot(
    resource_type: str = "cpu", quantity: Decimal = Decimal("4")
) -> ResourceSlotInfo:
    return ResourceSlotInfo(
        entries=[ResourceSlotEntryInfo(resource_type=resource_type, quantity=quantity)]
    )


def _make_fair_share_spec() -> FairShareSpecInfo:
    return FairShareSpecInfo(
        weight=Decimal("1.0"),
        half_life_days=30,
        lookback_days=90,
        decay_unit_days=1,
        resource_weights=[
            ResourceWeightEntryInfo(resource_type="cpu", weight=Decimal("1.0"), uses_default=False)
        ],
    )


def _make_calculation_snapshot() -> FairShareCalculationSnapshotInfo:
    return FairShareCalculationSnapshotInfo(
        fair_share_factor=Decimal("0.25"),
        total_decayed_usage=_make_resource_slot(),
        normalized_usage=Decimal("100.0"),
        lookback_start=_DATE_START,
        lookback_end=_DATE_END,
        last_calculated_at=_NOW,
    )


def _make_usage_bucket_metadata() -> UsageBucketMetadataInfo:
    return UsageBucketMetadataInfo(
        period_start=date(2025, 3, 16),
        period_end=date(2025, 3, 17),
        decay_unit_days=1,
        created_at=_NOW,
        updated_at=_NOW,
        average_daily_usage=_make_resource_slot(),
        usage_capacity_ratio=_make_resource_slot(quantity=Decimal("0.5")),
    )


def _make_domain_fair_share_node() -> DomainFairShareNode:
    return DomainFairShareNode(
        id=str(_UUID1),
        resource_group_name="default",
        domain_name="test-domain",
        spec=_make_fair_share_spec(),
        calculation_snapshot=_make_calculation_snapshot(),
        created_at=_NOW,
        updated_at=_NOW,
    )


def _make_project_fair_share_node() -> ProjectFairShareNode:
    return ProjectFairShareNode(
        id=str(_UUID1),
        resource_group_name="default",
        project_id=_UUID2,
        domain_name="test-domain",
        spec=_make_fair_share_spec(),
        calculation_snapshot=_make_calculation_snapshot(),
        created_at=_NOW,
        updated_at=_NOW,
    )


def _make_user_fair_share_node() -> UserFairShareNode:
    return UserFairShareNode(
        id=str(_UUID1),
        resource_group_name="default",
        user_uuid=_UUID2,
        project_id=_UUID3,
        domain_name="test-domain",
        spec=_make_fair_share_spec(),
        calculation_snapshot=_make_calculation_snapshot(),
        created_at=_NOW,
        updated_at=_NOW,
    )


class TestDomainFairShareNode:
    """Tests for DomainFairShareNode model."""

    def test_creation_with_all_fields(self) -> None:
        node = _make_domain_fair_share_node()
        assert node.id == str(_UUID1)
        assert node.resource_group_name == "default"
        assert node.domain_name == "test-domain"

    def test_contains_nested_fair_share_spec(self) -> None:
        node = _make_domain_fair_share_node()
        assert isinstance(node.spec, FairShareSpecInfo)
        assert node.spec.half_life_days == 30
        assert node.spec.lookback_days == 90

    def test_contains_nested_calculation_snapshot(self) -> None:
        node = _make_domain_fair_share_node()
        assert isinstance(node.calculation_snapshot, FairShareCalculationSnapshotInfo)
        assert node.calculation_snapshot.fair_share_factor == Decimal("0.25")

    def test_missing_required_field_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DomainFairShareNode.model_validate({
                "id": str(_UUID1),
                "resource_group": "default",
                # missing domain_name, spec, calculation_snapshot, created_at, updated_at
            })

    def test_round_trip_serialization(self) -> None:
        node = _make_domain_fair_share_node()
        json_str = node.model_dump_json()
        restored = DomainFairShareNode.model_validate_json(json_str)
        assert restored.id == str(_UUID1)
        assert restored.domain_name == "test-domain"

    def test_round_trip_preserves_nested_spec(self) -> None:
        node = _make_domain_fair_share_node()
        json_str = node.model_dump_json()
        restored = DomainFairShareNode.model_validate_json(json_str)
        assert restored.spec.half_life_days == 30
        assert restored.spec.weight == Decimal("1.0")

    def test_round_trip_preserves_nested_snapshot(self) -> None:
        node = _make_domain_fair_share_node()
        json_str = node.model_dump_json()
        restored = DomainFairShareNode.model_validate_json(json_str)
        assert restored.calculation_snapshot.fair_share_factor == Decimal("0.25")

    def test_model_dump_json_includes_nested_fields(self) -> None:
        node = _make_domain_fair_share_node()
        data = json.loads(node.model_dump_json())
        assert "spec" in data
        assert "calculation_snapshot" in data
        assert "half_life_days" in data["spec"]
        assert "fair_share_factor" in data["calculation_snapshot"]


class TestProjectFairShareNode:
    """Tests for ProjectFairShareNode model."""

    def test_creation_with_all_fields(self) -> None:
        node = _make_project_fair_share_node()
        assert node.id == str(_UUID1)
        assert node.project_id == _UUID2
        assert node.domain_name == "test-domain"

    def test_contains_nested_spec_and_snapshot(self) -> None:
        node = _make_project_fair_share_node()
        assert isinstance(node.spec, FairShareSpecInfo)
        assert isinstance(node.calculation_snapshot, FairShareCalculationSnapshotInfo)

    def test_round_trip_serialization(self) -> None:
        node = _make_project_fair_share_node()
        json_str = node.model_dump_json()
        restored = ProjectFairShareNode.model_validate_json(json_str)
        assert restored.project_id == _UUID2


class TestUserFairShareNode:
    """Tests for UserFairShareNode model."""

    def test_creation_with_all_fields(self) -> None:
        node = _make_user_fair_share_node()
        assert node.user_uuid == _UUID2
        assert node.project_id == _UUID3
        assert node.domain_name == "test-domain"

    def test_contains_nested_spec_and_snapshot(self) -> None:
        node = _make_user_fair_share_node()
        assert isinstance(node.spec, FairShareSpecInfo)
        assert isinstance(node.calculation_snapshot, FairShareCalculationSnapshotInfo)

    def test_round_trip_serialization(self) -> None:
        node = _make_user_fair_share_node()
        json_str = node.model_dump_json()
        restored = UserFairShareNode.model_validate_json(json_str)
        assert restored.user_uuid == _UUID2
        assert restored.project_id == _UUID3


class TestDomainUsageBucketNode:
    """Tests for DomainUsageBucketNode model."""

    def test_creation_with_all_fields(self) -> None:
        node = DomainUsageBucketNode(
            id=_UUID1,
            domain_name="test-domain",
            resource_group="default",
            metadata=_make_usage_bucket_metadata(),
            resource_usage=_make_resource_slot(),
            capacity_snapshot=_make_resource_slot(quantity=Decimal("16")),
        )
        assert node.id == _UUID1
        assert node.domain_name == "test-domain"
        assert node.resource_group == "default"

    def test_contains_nested_metadata(self) -> None:
        node = DomainUsageBucketNode(
            id=_UUID1,
            domain_name="test-domain",
            resource_group="default",
            metadata=_make_usage_bucket_metadata(),
            resource_usage=_make_resource_slot(),
            capacity_snapshot=_make_resource_slot(quantity=Decimal("16")),
        )
        assert isinstance(node.metadata, UsageBucketMetadataInfo)
        assert isinstance(node.resource_usage, ResourceSlotInfo)

    def test_round_trip_serialization(self) -> None:
        node = DomainUsageBucketNode(
            id=_UUID1,
            domain_name="test-domain",
            resource_group="default",
            metadata=_make_usage_bucket_metadata(),
            resource_usage=_make_resource_slot(),
            capacity_snapshot=_make_resource_slot(quantity=Decimal("16")),
        )
        json_str = node.model_dump_json()
        restored = DomainUsageBucketNode.model_validate_json(json_str)
        assert restored.id == _UUID1
        assert restored.domain_name == "test-domain"


class TestProjectUsageBucketNode:
    """Tests for ProjectUsageBucketNode model."""

    def test_creation_with_all_fields(self) -> None:
        node = ProjectUsageBucketNode(
            id=_UUID1,
            project_id=_UUID2,
            domain_name="test-domain",
            resource_group="default",
            metadata=_make_usage_bucket_metadata(),
            resource_usage=_make_resource_slot(),
            capacity_snapshot=_make_resource_slot(quantity=Decimal("16")),
        )
        assert node.project_id == _UUID2


class TestUserUsageBucketNode:
    """Tests for UserUsageBucketNode model."""

    def test_creation_with_all_fields(self) -> None:
        node = UserUsageBucketNode(
            id=_UUID1,
            user_uuid=_UUID2,
            project_id=_UUID3,
            domain_name="test-domain",
            resource_group="default",
            metadata=_make_usage_bucket_metadata(),
            resource_usage=_make_resource_slot(),
            capacity_snapshot=_make_resource_slot(quantity=Decimal("16")),
        )
        assert node.user_uuid == _UUID2
        assert node.project_id == _UUID3


class TestResourceGroupFairShareSpecNode:
    """Tests for ResourceGroupFairShareSpecNode model."""

    def test_creation_with_all_fields(self) -> None:
        node = ResourceGroupFairShareSpecNode(
            half_life_days=30,
            lookback_days=90,
            decay_unit_days=1,
            default_weight=Decimal("1.0"),
            resource_weights=_make_resource_slot(),
        )
        assert node.half_life_days == 30
        assert node.lookback_days == 90
        assert node.default_weight == Decimal("1.0")

    def test_nested_resource_weights(self) -> None:
        node = ResourceGroupFairShareSpecNode(
            half_life_days=14,
            lookback_days=60,
            decay_unit_days=1,
            default_weight=Decimal("1.0"),
            resource_weights=_make_resource_slot(),
        )
        assert isinstance(node.resource_weights, ResourceSlotInfo)

    def test_round_trip_serialization(self) -> None:
        node = ResourceGroupFairShareSpecNode(
            half_life_days=30,
            lookback_days=90,
            decay_unit_days=1,
            default_weight=Decimal("2.0"),
            resource_weights=_make_resource_slot(),
        )
        json_str = node.model_dump_json()
        restored = ResourceGroupFairShareSpecNode.model_validate_json(json_str)
        assert restored.half_life_days == 30
        assert restored.default_weight == Decimal("2.0")


class TestGetDomainFairSharePayload:
    """Tests for GetDomainFairSharePayload model."""

    def test_creation_with_node(self) -> None:
        node = _make_domain_fair_share_node()
        payload = GetDomainFairSharePayload(item=node)
        assert payload.item is not None
        assert payload.item.domain_name == "test-domain"

    def test_creation_with_none(self) -> None:
        payload = GetDomainFairSharePayload(item=None)
        assert payload.item is None

    def test_default_item_is_none(self) -> None:
        payload = GetDomainFairSharePayload()
        assert payload.item is None


class TestGetProjectFairSharePayload:
    """Tests for GetProjectFairSharePayload model."""

    def test_creation_with_node(self) -> None:
        node = _make_project_fair_share_node()
        payload = GetProjectFairSharePayload(item=node)
        assert payload.item is not None

    def test_creation_with_none(self) -> None:
        payload = GetProjectFairSharePayload(item=None)
        assert payload.item is None


class TestGetUserFairSharePayload:
    """Tests for GetUserFairSharePayload model."""

    def test_creation_with_none(self) -> None:
        payload = GetUserFairSharePayload(item=None)
        assert payload.item is None


class TestSearchDomainFairSharesPayload:
    """Tests for SearchDomainFairSharesPayload model."""

    def test_creation_with_empty_list(self) -> None:
        payload = SearchDomainFairSharesPayload(items=[], total_count=0)
        assert payload.items == []
        assert payload.total_count == 0

    def test_creation_with_items(self) -> None:
        nodes = [_make_domain_fair_share_node()]
        payload = SearchDomainFairSharesPayload(items=nodes, total_count=1)
        assert len(payload.items) == 1
        assert payload.total_count == 1

    def test_missing_total_count_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchDomainFairSharesPayload.model_validate({"items": []})

    def test_round_trip_serialization(self) -> None:
        nodes = [_make_domain_fair_share_node()]
        payload = SearchDomainFairSharesPayload(items=nodes, total_count=1)
        json_str = payload.model_dump_json()
        restored = SearchDomainFairSharesPayload.model_validate_json(json_str)
        assert restored.total_count == 1
        assert len(restored.items) == 1
        assert restored.items[0].domain_name == "test-domain"


class TestSearchProjectFairSharesPayload:
    """Tests for SearchProjectFairSharesPayload model."""

    def test_creation_with_empty_list(self) -> None:
        payload = SearchProjectFairSharesPayload(items=[], total_count=0)
        assert payload.total_count == 0


class TestSearchUserFairSharesPayload:
    """Tests for SearchUserFairSharesPayload model."""

    def test_creation_with_empty_list(self) -> None:
        payload = SearchUserFairSharesPayload(items=[], total_count=0)
        assert payload.total_count == 0


class TestSearchDomainUsageBucketsPayload:
    """Tests for SearchDomainUsageBucketsPayload model."""

    def test_creation_with_empty_list(self) -> None:
        payload = SearchDomainUsageBucketsPayload(items=[], total_count=0)
        assert payload.total_count == 0


class TestSearchProjectUsageBucketsPayload:
    """Tests for SearchProjectUsageBucketsPayload model."""

    def test_creation_with_empty_list(self) -> None:
        payload = SearchProjectUsageBucketsPayload(items=[], total_count=0)
        assert payload.total_count == 0


class TestSearchUserUsageBucketsPayload:
    """Tests for SearchUserUsageBucketsPayload model."""

    def test_creation_with_empty_list(self) -> None:
        payload = SearchUserUsageBucketsPayload(items=[], total_count=0)
        assert payload.total_count == 0


class TestUpsertDomainFairShareWeightPayload:
    """Tests for UpsertDomainFairShareWeightPayload model."""

    def test_creation_with_node(self) -> None:
        node = _make_domain_fair_share_node()
        payload = UpsertDomainFairShareWeightPayload(domain_fair_share=node)
        assert isinstance(payload.domain_fair_share, DomainFairShareNode)

    def test_round_trip_serialization(self) -> None:
        node = _make_domain_fair_share_node()
        payload = UpsertDomainFairShareWeightPayload(domain_fair_share=node)
        json_str = payload.model_dump_json()
        restored = UpsertDomainFairShareWeightPayload.model_validate_json(json_str)
        assert restored.domain_fair_share.domain_name == "test-domain"


class TestUpsertProjectFairShareWeightPayload:
    """Tests for UpsertProjectFairShareWeightPayload model."""

    def test_creation_with_node(self) -> None:
        node = _make_project_fair_share_node()
        payload = UpsertProjectFairShareWeightPayload(project_fair_share=node)
        assert isinstance(payload.project_fair_share, ProjectFairShareNode)


class TestUpsertUserFairShareWeightPayload:
    """Tests for UpsertUserFairShareWeightPayload model."""

    def test_creation_with_node(self) -> None:
        node = _make_user_fair_share_node()
        payload = UpsertUserFairShareWeightPayload(user_fair_share=node)
        assert isinstance(payload.user_fair_share, UserFairShareNode)


class TestBulkUpsertDomainFairShareWeightPayload:
    """Tests for BulkUpsertDomainFairShareWeightPayload model."""

    def test_creation(self) -> None:
        payload = BulkUpsertDomainFairShareWeightPayload(upserted_count=3)
        assert payload.upserted_count == 3

    def test_missing_upserted_count_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            BulkUpsertDomainFairShareWeightPayload.model_validate({})

    def test_round_trip_serialization(self) -> None:
        payload = BulkUpsertDomainFairShareWeightPayload(upserted_count=5)
        json_str = payload.model_dump_json()
        restored = BulkUpsertDomainFairShareWeightPayload.model_validate_json(json_str)
        assert restored.upserted_count == 5


class TestBulkUpsertProjectFairShareWeightPayload:
    """Tests for BulkUpsertProjectFairShareWeightPayload model."""

    def test_creation(self) -> None:
        payload = BulkUpsertProjectFairShareWeightPayload(upserted_count=2)
        assert payload.upserted_count == 2


class TestBulkUpsertUserFairShareWeightPayload:
    """Tests for BulkUpsertUserFairShareWeightPayload model."""

    def test_creation(self) -> None:
        payload = BulkUpsertUserFairShareWeightPayload(upserted_count=10)
        assert payload.upserted_count == 10


class TestUpdateResourceGroupFairShareSpecPayload:
    """Tests for UpdateResourceGroupFairShareSpecPayload model."""

    def test_creation(self) -> None:
        spec_node = ResourceGroupFairShareSpecNode(
            half_life_days=30,
            lookback_days=90,
            decay_unit_days=1,
            default_weight=Decimal("1.0"),
            resource_weights=_make_resource_slot(),
        )
        payload = UpdateResourceGroupFairShareSpecPayload(
            resource_group="default",
            fair_share_spec=spec_node,
        )
        assert payload.resource_group == "default"
        assert payload.fair_share_spec.half_life_days == 30

    def test_round_trip_serialization(self) -> None:
        spec_node = ResourceGroupFairShareSpecNode(
            half_life_days=14,
            lookback_days=60,
            decay_unit_days=1,
            default_weight=Decimal("2.0"),
            resource_weights=_make_resource_slot(),
        )
        payload = UpdateResourceGroupFairShareSpecPayload(
            resource_group="sg1",
            fair_share_spec=spec_node,
        )
        json_str = payload.model_dump_json()
        restored = UpdateResourceGroupFairShareSpecPayload.model_validate_json(json_str)
        assert restored.resource_group == "sg1"
        assert restored.fair_share_spec.half_life_days == 14


class TestGetResourceGroupFairShareSpecPayload:
    """Tests for GetResourceGroupFairShareSpecPayload model."""

    def test_creation(self) -> None:
        spec_node = ResourceGroupFairShareSpecNode(
            half_life_days=30,
            lookback_days=90,
            decay_unit_days=1,
            default_weight=Decimal("1.0"),
            resource_weights=_make_resource_slot(),
        )
        payload = GetResourceGroupFairShareSpecPayload(
            resource_group="default",
            fair_share_spec=spec_node,
        )
        assert payload.resource_group == "default"
        assert isinstance(payload.fair_share_spec, ResourceGroupFairShareSpecNode)
