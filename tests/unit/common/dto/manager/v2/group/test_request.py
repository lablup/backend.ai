"""Tests for ai.backend.common.dto.manager.v2.group.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.dto.manager.v2.group.request import (
    CreateProjectInput,
    DeleteProjectInput,
    ProjectFilter,
    ProjectOrder,
    PurgeProjectInput,
    SearchProjectsRequest,
    UpdateProjectInput,
)
from ai.backend.common.dto.manager.v2.group.types import OrderDirection, ProjectOrderField


class TestCreateProjectInput:
    """Tests for CreateProjectInput model creation and validation."""

    def test_valid_creation_with_required_fields(self) -> None:
        req = CreateProjectInput(name="test-group", domain_name="default")
        assert req.name == "test-group"
        assert req.domain_name == "default"
        assert req.description is None
        assert req.integration_id is None
        assert req.resource_policy is None

    def test_valid_creation_with_all_fields(self) -> None:
        req = CreateProjectInput(
            name="research-group",
            domain_name="research-domain",
            description="Research team group",
            integration_id="ext-456",
            resource_policy="research-policy",
        )
        assert req.description == "Research team group"
        assert req.integration_id == "ext-456"
        assert req.resource_policy == "research-policy"

    def test_name_max_length_64_enforced(self) -> None:
        with pytest.raises(ValidationError):
            CreateProjectInput(name="a" * 65, domain_name="default")

    def test_name_at_max_length_valid(self) -> None:
        req = CreateProjectInput(name="a" * 64, domain_name="default")
        assert len(req.name) == 64

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateProjectInput.model_validate({"domain_name": "default"})

    def test_missing_domain_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateProjectInput.model_validate({"name": "group"})

    def test_round_trip_serialization(self) -> None:
        req = CreateProjectInput(
            name="my-group",
            domain_name="my-domain",
            description="My group",
        )
        json_data = req.model_dump_json()
        restored = CreateProjectInput.model_validate_json(json_data)
        assert restored.name == req.name
        assert restored.domain_name == req.domain_name
        assert restored.description == req.description


class TestUpdateProjectInput:
    """Tests for UpdateProjectInput model with SENTINEL fields."""

    def test_empty_update_has_sentinel_defaults(self) -> None:
        req = UpdateProjectInput()
        assert req.description is SENTINEL
        assert isinstance(req.description, Sentinel)
        assert req.integration_id is SENTINEL
        assert isinstance(req.integration_id, Sentinel)

    def test_non_sentinel_fields_default_to_none(self) -> None:
        req = UpdateProjectInput()
        assert req.name is None
        assert req.is_active is None
        assert req.resource_policy is None

    def test_explicit_none_description_signals_clear(self) -> None:
        req = UpdateProjectInput(description=None)
        assert req.description is None

    def test_string_description_update(self) -> None:
        req = UpdateProjectInput(description="New description")
        assert req.description == "New description"

    def test_name_update(self) -> None:
        req = UpdateProjectInput(name="new-group-name")
        assert req.name == "new-group-name"

    def test_name_max_length_enforced(self) -> None:
        with pytest.raises(ValidationError):
            UpdateProjectInput(name="a" * 65)

    def test_is_active_update(self) -> None:
        req = UpdateProjectInput(is_active=False)
        assert req.is_active is False

    def test_integration_id_none_clears(self) -> None:
        req = UpdateProjectInput(integration_id=None)
        assert req.integration_id is None

    def test_integration_id_string_update(self) -> None:
        req = UpdateProjectInput(integration_id="new-ext-id")
        assert req.integration_id == "new-ext-id"

    def test_resource_policy_update(self) -> None:
        req = UpdateProjectInput(resource_policy="new-policy")
        assert req.resource_policy == "new-policy"

    def test_round_trip_with_none_fields(self) -> None:
        req = UpdateProjectInput(
            name="updated",
            description=None,
            is_active=True,
            integration_id=None,
        )
        json_data = req.model_dump_json()
        restored = UpdateProjectInput.model_validate_json(json_data)
        assert restored.name == "updated"
        assert restored.description is None
        assert restored.is_active is True
        assert restored.integration_id is None


class TestDeleteProjectInput:
    """Tests for DeleteProjectInput model."""

    def test_valid_creation_with_uuid(self) -> None:
        group_id = uuid.uuid4()
        req = DeleteProjectInput(group_id=group_id)
        assert req.group_id == group_id

    def test_valid_creation_from_uuid_string(self) -> None:
        group_id = uuid.uuid4()
        req = DeleteProjectInput.model_validate({"group_id": str(group_id)})
        assert req.group_id == group_id

    def test_invalid_uuid_raises(self) -> None:
        with pytest.raises(ValidationError):
            DeleteProjectInput.model_validate({"group_id": "not-a-uuid"})

    def test_missing_group_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            DeleteProjectInput.model_validate({})

    def test_round_trip(self) -> None:
        group_id = uuid.uuid4()
        req = DeleteProjectInput(group_id=group_id)
        json_data = req.model_dump_json()
        restored = DeleteProjectInput.model_validate_json(json_data)
        assert restored.group_id == group_id


class TestPurgeProjectInput:
    """Tests for PurgeProjectInput model."""

    def test_valid_creation_with_uuid(self) -> None:
        group_id = uuid.uuid4()
        req = PurgeProjectInput(group_id=group_id)
        assert req.group_id == group_id

    def test_valid_creation_from_uuid_string(self) -> None:
        group_id = uuid.uuid4()
        req = PurgeProjectInput.model_validate({"group_id": str(group_id)})
        assert req.group_id == group_id

    def test_invalid_uuid_raises(self) -> None:
        with pytest.raises(ValidationError):
            PurgeProjectInput.model_validate({"group_id": "not-a-uuid"})

    def test_round_trip(self) -> None:
        group_id = uuid.uuid4()
        req = PurgeProjectInput(group_id=group_id)
        json_data = req.model_dump_json()
        restored = PurgeProjectInput.model_validate_json(json_data)
        assert restored.group_id == group_id


class TestProjectFilter:
    """Tests for ProjectFilter model."""

    def test_empty_filter(self) -> None:
        f = ProjectFilter()
        assert f.name is None
        assert f.domain_name is None
        assert f.is_active is None

    def test_is_active_true(self) -> None:
        f = ProjectFilter(is_active=True)
        assert f.is_active is True

    def test_is_active_false(self) -> None:
        f = ProjectFilter(is_active=False)
        assert f.is_active is False

    def test_round_trip(self) -> None:
        f = ProjectFilter(is_active=True)
        json_data = f.model_dump_json()
        restored = ProjectFilter.model_validate_json(json_data)
        assert restored.is_active is True


class TestProjectOrder:
    """Tests for ProjectOrder model."""

    def test_default_direction_is_asc(self) -> None:
        order = ProjectOrder(field=ProjectOrderField.NAME)
        assert order.direction == OrderDirection.ASC

    def test_explicit_desc_direction(self) -> None:
        order = ProjectOrder(field=ProjectOrderField.CREATED_AT, direction=OrderDirection.DESC)
        assert order.direction == OrderDirection.DESC

    def test_round_trip(self) -> None:
        order = ProjectOrder(field=ProjectOrderField.MODIFIED_AT, direction=OrderDirection.DESC)
        json_data = order.model_dump_json()
        restored = ProjectOrder.model_validate_json(json_data)
        assert restored.field == ProjectOrderField.MODIFIED_AT
        assert restored.direction == OrderDirection.DESC


class TestSearchProjectsRequest:
    """Tests for SearchProjectsRequest model."""

    def test_defaults(self) -> None:
        req = SearchProjectsRequest()
        assert req.filter is None
        assert req.order is None
        assert req.offset == 0

    def test_limit_default_is_positive(self) -> None:
        req = SearchProjectsRequest()
        assert req.limit >= 1

    def test_limit_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchProjectsRequest(limit=0)

    def test_negative_offset_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchProjectsRequest(offset=-1)

    def test_with_filter_and_order(self) -> None:
        req = SearchProjectsRequest(
            filter=ProjectFilter(is_active=True),
            order=[ProjectOrder(field=ProjectOrderField.NAME)],
            limit=10,
            offset=20,
        )
        assert req.filter is not None
        assert req.filter.is_active is True
        assert req.order is not None
        assert len(req.order) == 1
        assert req.limit == 10
        assert req.offset == 20

    def test_round_trip(self) -> None:
        req = SearchProjectsRequest(
            filter=ProjectFilter(is_active=False),
            limit=5,
            offset=0,
        )
        json_data = req.model_dump_json()
        restored = SearchProjectsRequest.model_validate_json(json_data)
        assert restored.filter is not None
        assert restored.filter.is_active is False
        assert restored.limit == 5
