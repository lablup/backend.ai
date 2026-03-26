"""Tests for ai.backend.common.dto.manager.v2.fair_share.request module."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.fair_share.request import (
    BulkUpsertDomainFairShareWeightInput,
    BulkUpsertProjectFairShareWeightInput,
    BulkUpsertUserFairShareWeightInput,
    DomainFairShareFilter,
    DomainFairShareOrder,
    DomainWeightEntryInput,
    GetDomainFairShareInput,
    GetProjectFairShareInput,
    GetResourceGroupFairShareSpecInput,
    GetUserFairShareInput,
    ProjectFairShareFilter,
    ProjectFairShareOrder,
    ProjectWeightEntryInput,
    ResourceWeightEntryInput,
    SearchDomainFairSharesInput,
    SearchDomainUsageBucketsInput,
    SearchProjectFairSharesInput,
    SearchProjectUsageBucketsInput,
    SearchUserFairSharesInput,
    SearchUserUsageBucketsInput,
    UpdateResourceGroupFairShareSpecInput,
    UpsertDomainFairShareWeightInput,
    UpsertProjectFairShareWeightInput,
    UpsertUserFairShareWeightInput,
    UserFairShareFilter,
    UserFairShareOrder,
    UserWeightEntryInput,
)
from ai.backend.common.dto.manager.v2.fair_share.types import (
    DomainFairShareOrderField,
    OrderDirection,
    ProjectFairShareOrderField,
    UserFairShareOrderField,
)

_SAMPLE_UUID = UUID("550e8400-e29b-41d4-a716-446655440000")
_SAMPLE_UUID2 = UUID("660e8400-e29b-41d4-a716-446655440001")


class TestDomainFairShareFilter:
    """Tests for DomainFairShareFilter model."""

    def test_creation_with_no_filters(self) -> None:
        f = DomainFairShareFilter()
        assert f.resource_group is None
        assert f.domain_name is None

    def test_creation_from_dict(self) -> None:
        f = DomainFairShareFilter.model_validate({})
        assert f.resource_group is None
        assert f.domain_name is None


class TestProjectFairShareFilter:
    """Tests for ProjectFairShareFilter model."""

    def test_creation_with_no_filters(self) -> None:
        f = ProjectFairShareFilter()
        assert f.resource_group is None
        assert f.project_id is None
        assert f.domain_name is None


class TestUserFairShareFilter:
    """Tests for UserFairShareFilter model."""

    def test_creation_with_no_filters(self) -> None:
        f = UserFairShareFilter()
        assert f.resource_group is None
        assert f.user_uuid is None
        assert f.project_id is None
        assert f.domain_name is None


class TestDomainFairShareOrder:
    """Tests for DomainFairShareOrder model."""

    def test_creation_with_field(self) -> None:
        order = DomainFairShareOrder(field=DomainFairShareOrderField.FAIR_SHARE_FACTOR)
        assert order.field == DomainFairShareOrderField.FAIR_SHARE_FACTOR

    def test_default_direction_is_desc(self) -> None:
        order = DomainFairShareOrder(field=DomainFairShareOrderField.DOMAIN_NAME)
        assert order.direction == OrderDirection.DESC

    def test_explicit_direction(self) -> None:
        order = DomainFairShareOrder(
            field=DomainFairShareOrderField.CREATED_AT,
            direction=OrderDirection.ASC,
        )
        assert order.direction == OrderDirection.ASC


class TestProjectFairShareOrder:
    """Tests for ProjectFairShareOrder model."""

    def test_default_direction_is_desc(self) -> None:
        order = ProjectFairShareOrder(field=ProjectFairShareOrderField.FAIR_SHARE_FACTOR)
        assert order.direction == OrderDirection.DESC


class TestUserFairShareOrder:
    """Tests for UserFairShareOrder model."""

    def test_default_direction_is_desc(self) -> None:
        order = UserFairShareOrder(field=UserFairShareOrderField.FAIR_SHARE_FACTOR)
        assert order.direction == OrderDirection.DESC


class TestGetDomainFairShareInput:
    """Tests for GetDomainFairShareInput model."""

    def test_valid_creation(self) -> None:
        inp = GetDomainFairShareInput(resource_group="default", domain_name="test-domain")
        assert inp.resource_group == "default"
        assert inp.domain_name == "test-domain"

    def test_missing_resource_group_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            GetDomainFairShareInput.model_validate({"domain_name": "test"})

    def test_missing_domain_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            GetDomainFairShareInput.model_validate({"resource_group": "default"})

    def test_round_trip_serialization(self) -> None:
        inp = GetDomainFairShareInput(resource_group="sg1", domain_name="domain1")
        json_str = inp.model_dump_json()
        restored = GetDomainFairShareInput.model_validate_json(json_str)
        assert restored.resource_group == "sg1"
        assert restored.domain_name == "domain1"


class TestGetProjectFairShareInput:
    """Tests for GetProjectFairShareInput model."""

    def test_valid_creation(self) -> None:
        inp = GetProjectFairShareInput(resource_group="default", project_id=_SAMPLE_UUID)
        assert inp.resource_group == "default"
        assert inp.project_id == _SAMPLE_UUID

    def test_missing_project_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            GetProjectFairShareInput.model_validate({"resource_group": "default"})


class TestGetUserFairShareInput:
    """Tests for GetUserFairShareInput model."""

    def test_valid_creation(self) -> None:
        inp = GetUserFairShareInput(
            resource_group="default",
            project_id=_SAMPLE_UUID,
            user_uuid=_SAMPLE_UUID2,
        )
        assert inp.resource_group == "default"
        assert inp.project_id == _SAMPLE_UUID
        assert inp.user_uuid == _SAMPLE_UUID2

    def test_missing_user_uuid_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            GetUserFairShareInput.model_validate({
                "resource_group": "default",
                "project_id": str(_SAMPLE_UUID),
            })


class TestGetResourceGroupFairShareSpecInput:
    """Tests for GetResourceGroupFairShareSpecInput model."""

    def test_valid_creation(self) -> None:
        inp = GetResourceGroupFairShareSpecInput(resource_group="default")
        assert inp.resource_group == "default"

    def test_missing_resource_group_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            GetResourceGroupFairShareSpecInput.model_validate({})


class TestSearchDomainFairSharesInput:
    """Tests for SearchDomainFairSharesInput model."""

    def test_default_values(self) -> None:
        inp = SearchDomainFairSharesInput()
        assert inp.filter is None
        assert inp.order is None
        assert inp.limit is None
        assert inp.offset is None

    def test_custom_limit_and_offset(self) -> None:
        inp = SearchDomainFairSharesInput(limit=100, offset=10)
        assert inp.limit == 100
        assert inp.offset == 10

    def test_limit_min_boundary(self) -> None:
        inp = SearchDomainFairSharesInput(limit=1)
        assert inp.limit == 1

    def test_limit_max_boundary(self) -> None:
        inp = SearchDomainFairSharesInput(limit=1000)
        assert inp.limit == 1000

    def test_limit_exceeds_max_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchDomainFairSharesInput(limit=1001)

    def test_limit_below_min_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchDomainFairSharesInput(limit=0)

    def test_offset_negative_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchDomainFairSharesInput(offset=-1)

    def test_with_order(self) -> None:
        order = DomainFairShareOrder(field=DomainFairShareOrderField.DOMAIN_NAME)
        inp = SearchDomainFairSharesInput(order=[order])
        assert inp.order is not None
        assert len(inp.order) == 1
        assert inp.order[0].field == DomainFairShareOrderField.DOMAIN_NAME


class TestSearchProjectFairSharesInput:
    """Tests for SearchProjectFairSharesInput model."""

    def test_default_values(self) -> None:
        inp = SearchProjectFairSharesInput()
        assert inp.limit is None
        assert inp.offset is None
        assert inp.filter is None


class TestSearchUserFairSharesInput:
    """Tests for SearchUserFairSharesInput model."""

    def test_default_values(self) -> None:
        inp = SearchUserFairSharesInput()
        assert inp.limit is None
        assert inp.offset is None


class TestSearchDomainUsageBucketsInput:
    """Tests for SearchDomainUsageBucketsInput model."""

    def test_default_values(self) -> None:
        inp = SearchDomainUsageBucketsInput()
        assert inp.limit == 50
        assert inp.offset == 0


class TestSearchProjectUsageBucketsInput:
    """Tests for SearchProjectUsageBucketsInput model."""

    def test_default_values(self) -> None:
        inp = SearchProjectUsageBucketsInput()
        assert inp.limit == 50
        assert inp.offset == 0


class TestSearchUserUsageBucketsInput:
    """Tests for SearchUserUsageBucketsInput model."""

    def test_default_values(self) -> None:
        inp = SearchUserUsageBucketsInput()
        assert inp.limit == 50
        assert inp.offset == 0


class TestUpsertDomainFairShareWeightInput:
    """Tests for UpsertDomainFairShareWeightInput model."""

    def test_weight_none_is_valid(self) -> None:
        inp = UpsertDomainFairShareWeightInput(
            resource_group_name="default", domain_name="test", weight=None
        )
        assert inp.weight is None

    def test_default_weight_is_none(self) -> None:
        inp = UpsertDomainFairShareWeightInput(resource_group_name="default", domain_name="test")
        assert inp.weight is None

    def test_weight_with_value(self) -> None:
        inp = UpsertDomainFairShareWeightInput(
            resource_group_name="default", domain_name="test", weight=Decimal("1.5")
        )
        assert inp.weight == Decimal("1.5")

    def test_round_trip_serialization(self) -> None:
        inp = UpsertDomainFairShareWeightInput(
            resource_group_name="default", domain_name="test", weight=Decimal("2.0")
        )
        json_str = inp.model_dump_json()
        restored = UpsertDomainFairShareWeightInput.model_validate_json(json_str)
        assert restored.weight == Decimal("2.0")

    def test_round_trip_with_none_weight(self) -> None:
        inp = UpsertDomainFairShareWeightInput(
            resource_group_name="default", domain_name="test", weight=None
        )
        json_str = inp.model_dump_json()
        restored = UpsertDomainFairShareWeightInput.model_validate_json(json_str)
        assert restored.weight is None


class TestUpsertProjectFairShareWeightInput:
    """Tests for UpsertProjectFairShareWeightInput model."""

    def test_valid_creation(self) -> None:
        inp = UpsertProjectFairShareWeightInput(
            resource_group_name="default",
            project_id=_SAMPLE_UUID,
            domain_name="test",
            weight=None,
        )
        assert inp.domain_name == "test"
        assert inp.weight is None

    def test_weight_with_value(self) -> None:
        inp = UpsertProjectFairShareWeightInput(
            resource_group_name="default",
            project_id=_SAMPLE_UUID,
            domain_name="test",
            weight=Decimal("0.5"),
        )
        assert inp.weight == Decimal("0.5")

    def test_missing_domain_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpsertProjectFairShareWeightInput.model_validate({"weight": None})


class TestUpsertUserFairShareWeightInput:
    """Tests for UpsertUserFairShareWeightInput model."""

    def test_valid_creation(self) -> None:
        inp = UpsertUserFairShareWeightInput(
            resource_group_name="default",
            user_uuid=_SAMPLE_UUID,
            project_id=_SAMPLE_UUID2,
            domain_name="test",
            weight=None,
        )
        assert inp.domain_name == "test"
        assert inp.weight is None

    def test_weight_with_value(self) -> None:
        inp = UpsertUserFairShareWeightInput(
            resource_group_name="default",
            user_uuid=_SAMPLE_UUID,
            project_id=_SAMPLE_UUID2,
            domain_name="test",
            weight=Decimal("3.0"),
        )
        assert inp.weight == Decimal("3.0")


class TestDomainWeightEntryInput:
    """Tests for DomainWeightEntryInput model."""

    def test_creation_with_weight(self) -> None:
        entry = DomainWeightEntryInput(domain_name="domain-a", weight=Decimal("1.0"))
        assert entry.domain_name == "domain-a"
        assert entry.weight == Decimal("1.0")

    def test_creation_with_none_weight(self) -> None:
        entry = DomainWeightEntryInput(domain_name="domain-b", weight=None)
        assert entry.weight is None


class TestBulkUpsertDomainFairShareWeightInput:
    """Tests for BulkUpsertDomainFairShareWeightInput model."""

    def test_valid_creation(self) -> None:
        entries = [
            DomainWeightEntryInput(domain_name="domain-a", weight=Decimal("1.0")),
            DomainWeightEntryInput(domain_name="domain-b", weight=None),
        ]
        inp = BulkUpsertDomainFairShareWeightInput(resource_group_name="default", inputs=entries)
        assert inp.resource_group_name == "default"
        assert len(inp.inputs) == 2

    def test_empty_inputs_list(self) -> None:
        inp = BulkUpsertDomainFairShareWeightInput(resource_group_name="default", inputs=[])
        assert inp.inputs == []

    def test_missing_resource_group_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            BulkUpsertDomainFairShareWeightInput.model_validate({"inputs": []})


class TestProjectWeightEntryInput:
    """Tests for ProjectWeightEntryInput model."""

    def test_creation_with_all_fields(self) -> None:
        entry = ProjectWeightEntryInput(
            project_id=_SAMPLE_UUID,
            domain_name="test",
            weight=Decimal("2.0"),
        )
        assert entry.project_id == _SAMPLE_UUID
        assert entry.domain_name == "test"
        assert entry.weight == Decimal("2.0")

    def test_creation_with_none_weight(self) -> None:
        entry = ProjectWeightEntryInput(
            project_id=_SAMPLE_UUID,
            domain_name="test",
            weight=None,
        )
        assert entry.weight is None


class TestBulkUpsertProjectFairShareWeightInput:
    """Tests for BulkUpsertProjectFairShareWeightInput model."""

    def test_valid_creation(self) -> None:
        entries = [
            ProjectWeightEntryInput(
                project_id=_SAMPLE_UUID,
                domain_name="domain-a",
                weight=Decimal("1.5"),
            )
        ]
        inp = BulkUpsertProjectFairShareWeightInput(resource_group_name="default", inputs=entries)
        assert inp.resource_group_name == "default"
        assert len(inp.inputs) == 1


class TestUserWeightEntryInput:
    """Tests for UserWeightEntryInput model."""

    def test_creation_with_all_fields(self) -> None:
        entry = UserWeightEntryInput(
            user_uuid=_SAMPLE_UUID,
            project_id=_SAMPLE_UUID2,
            domain_name="test",
            weight=Decimal("1.0"),
        )
        assert entry.user_uuid == _SAMPLE_UUID
        assert entry.project_id == _SAMPLE_UUID2
        assert entry.domain_name == "test"
        assert entry.weight == Decimal("1.0")


class TestBulkUpsertUserFairShareWeightInput:
    """Tests for BulkUpsertUserFairShareWeightInput model."""

    def test_valid_creation(self) -> None:
        entries = [
            UserWeightEntryInput(
                user_uuid=_SAMPLE_UUID,
                project_id=_SAMPLE_UUID2,
                domain_name="domain-a",
                weight=None,
            )
        ]
        inp = BulkUpsertUserFairShareWeightInput(resource_group_name="sg1", inputs=entries)
        assert inp.resource_group_name == "sg1"
        assert len(inp.inputs) == 1


class TestResourceWeightEntryInput:
    """Tests for ResourceWeightEntryInput model."""

    def test_creation_with_weight(self) -> None:
        entry = ResourceWeightEntryInput(resource_type="cpu", weight=Decimal("1.0"))
        assert entry.resource_type == "cpu"
        assert entry.weight == Decimal("1.0")

    def test_creation_with_none_weight(self) -> None:
        entry = ResourceWeightEntryInput(resource_type="mem", weight=None)
        assert entry.weight is None

    def test_default_weight_is_none(self) -> None:
        entry = ResourceWeightEntryInput(resource_type="cuda.shares")
        assert entry.weight is None


class TestUpdateResourceGroupFairShareSpecInput:
    """Tests for UpdateResourceGroupFairShareSpecInput model."""

    def test_all_fields_none_is_valid(self) -> None:
        inp = UpdateResourceGroupFairShareSpecInput()
        assert inp.half_life_days is None
        assert inp.lookback_days is None
        assert inp.decay_unit_days is None
        assert inp.default_weight is None
        assert inp.resource_weights is None

    def test_partial_update_with_some_fields(self) -> None:
        inp = UpdateResourceGroupFairShareSpecInput(half_life_days=14, lookback_days=60)
        assert inp.half_life_days == 14
        assert inp.lookback_days == 60
        assert inp.decay_unit_days is None

    def test_with_resource_weights(self) -> None:
        weights = [ResourceWeightEntryInput(resource_type="cpu", weight=Decimal("2.0"))]
        inp = UpdateResourceGroupFairShareSpecInput(resource_weights=weights)
        assert inp.resource_weights is not None
        assert len(inp.resource_weights) == 1
        assert inp.resource_weights[0].resource_type == "cpu"

    def test_with_default_weight(self) -> None:
        inp = UpdateResourceGroupFairShareSpecInput(default_weight=Decimal("1.0"))
        assert inp.default_weight == Decimal("1.0")

    def test_round_trip_serialization(self) -> None:
        inp = UpdateResourceGroupFairShareSpecInput(
            half_life_days=30,
            lookback_days=90,
        )
        json_str = inp.model_dump_json()
        restored = UpdateResourceGroupFairShareSpecInput.model_validate_json(json_str)
        assert restored.half_life_days == 30
        assert restored.lookback_days == 90
        assert restored.decay_unit_days is None
