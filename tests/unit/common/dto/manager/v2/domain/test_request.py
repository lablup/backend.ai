"""Tests for ai.backend.common.dto.manager.v2.domain.request module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.dto.manager.v2.domain.request import (
    CreateDomainInput,
    DeleteDomainInput,
    DomainFilter,
    DomainOrder,
    PurgeDomainInput,
    SearchDomainsRequest,
    UpdateDomainInput,
)
from ai.backend.common.dto.manager.v2.domain.types import DomainOrderField, OrderDirection


class TestCreateDomainInput:
    """Tests for CreateDomainInput model creation and validation."""

    def test_valid_creation_with_name_only(self) -> None:
        req = CreateDomainInput(name="test-domain")
        assert req.name == "test-domain"
        assert req.description is None
        assert req.is_active is True
        assert req.allowed_docker_registries is None
        assert req.integration_name is None

    def test_valid_creation_with_all_fields(self) -> None:
        req = CreateDomainInput(
            name="production",
            description="Production domain",
            is_active=True,
            allowed_docker_registries=["registry.example.com"],
            integration_name="ext-123",
        )
        assert req.name == "production"
        assert req.description == "Production domain"
        assert req.allowed_docker_registries == ["registry.example.com"]
        assert req.integration_name == "ext-123"

    def test_name_max_length_64_enforced(self) -> None:
        with pytest.raises(ValidationError):
            CreateDomainInput(name="a" * 65)

    def test_name_at_max_length_valid(self) -> None:
        req = CreateDomainInput(name="a" * 64)
        assert len(req.name) == 64

    def test_name_at_one_char_valid(self) -> None:
        req = CreateDomainInput(name="d")
        assert req.name == "d"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateDomainInput.model_validate({})

    def test_is_active_default_true(self) -> None:
        req = CreateDomainInput(name="domain")
        assert req.is_active is True

    def test_is_active_false(self) -> None:
        req = CreateDomainInput(name="domain", is_active=False)
        assert req.is_active is False

    def test_round_trip_serialization(self) -> None:
        req = CreateDomainInput(
            name="test-domain",
            description="Test",
            allowed_docker_registries=["registry.example.com"],
        )
        json_data = req.model_dump_json()
        restored = CreateDomainInput.model_validate_json(json_data)
        assert restored.name == req.name
        assert restored.description == req.description
        assert restored.allowed_docker_registries == req.allowed_docker_registries


class TestUpdateDomainInput:
    """Tests for UpdateDomainInput model with SENTINEL fields."""

    def test_empty_update_has_sentinel_defaults(self) -> None:
        req = UpdateDomainInput()
        assert req.description is SENTINEL
        assert isinstance(req.description, Sentinel)
        assert req.allowed_docker_registries is SENTINEL
        assert isinstance(req.allowed_docker_registries, Sentinel)
        assert req.integration_name is SENTINEL
        assert isinstance(req.integration_name, Sentinel)

    def test_non_sentinel_fields_default_to_none(self) -> None:
        req = UpdateDomainInput()
        assert req.name is None
        assert req.is_active is None

    def test_explicit_none_description_signals_clear(self) -> None:
        req = UpdateDomainInput(description=None)
        assert req.description is None

    def test_string_description_update(self) -> None:
        req = UpdateDomainInput(description="New description")
        assert req.description == "New description"

    def test_name_update(self) -> None:
        req = UpdateDomainInput(name="new-name")
        assert req.name == "new-name"

    def test_name_max_length_enforced(self) -> None:
        with pytest.raises(ValidationError):
            UpdateDomainInput(name="a" * 65)

    def test_is_active_update(self) -> None:
        req = UpdateDomainInput(is_active=False)
        assert req.is_active is False

    def test_allowed_docker_registries_none_clears(self) -> None:
        req = UpdateDomainInput(allowed_docker_registries=None)
        assert req.allowed_docker_registries is None

    def test_allowed_docker_registries_with_list(self) -> None:
        req = UpdateDomainInput(allowed_docker_registries=["reg1.example.com", "reg2.example.com"])
        assert req.allowed_docker_registries == ["reg1.example.com", "reg2.example.com"]

    def test_integration_name_none_clears(self) -> None:
        req = UpdateDomainInput(integration_name=None)
        assert req.integration_name is None

    def test_integration_name_string_update(self) -> None:
        req = UpdateDomainInput(integration_name="new-integration")
        assert req.integration_name == "new-integration"

    def test_round_trip_with_none_fields(self) -> None:
        req = UpdateDomainInput(
            name="updated-name",
            description=None,
            is_active=True,
            integration_name=None,
        )
        json_data = req.model_dump_json()
        restored = UpdateDomainInput.model_validate_json(json_data)
        assert restored.name == "updated-name"
        assert restored.description is None
        assert restored.is_active is True
        assert restored.integration_name is None


class TestDeleteDomainInput:
    """Tests for DeleteDomainInput model."""

    def test_valid_creation(self) -> None:
        req = DeleteDomainInput(name="test-domain")
        assert req.name == "test-domain"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            DeleteDomainInput.model_validate({})

    def test_round_trip(self) -> None:
        req = DeleteDomainInput(name="test-domain")
        json_data = req.model_dump_json()
        restored = DeleteDomainInput.model_validate_json(json_data)
        assert restored.name == "test-domain"


class TestPurgeDomainInput:
    """Tests for PurgeDomainInput model."""

    def test_valid_creation(self) -> None:
        req = PurgeDomainInput(name="test-domain")
        assert req.name == "test-domain"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            PurgeDomainInput.model_validate({})

    def test_round_trip(self) -> None:
        req = PurgeDomainInput(name="test-domain")
        json_data = req.model_dump_json()
        restored = PurgeDomainInput.model_validate_json(json_data)
        assert restored.name == "test-domain"


class TestDomainFilter:
    """Tests for DomainFilter model."""

    def test_empty_filter(self) -> None:
        f = DomainFilter()
        assert f.name is None
        assert f.is_active is None

    def test_is_active_true(self) -> None:
        f = DomainFilter(is_active=True)
        assert f.is_active is True

    def test_is_active_false(self) -> None:
        f = DomainFilter(is_active=False)
        assert f.is_active is False

    def test_round_trip(self) -> None:
        f = DomainFilter(is_active=True)
        json_data = f.model_dump_json()
        restored = DomainFilter.model_validate_json(json_data)
        assert restored.is_active is True


class TestDomainOrder:
    """Tests for DomainOrder model."""

    def test_default_direction_is_asc(self) -> None:
        order = DomainOrder(field=DomainOrderField.NAME)
        assert order.direction == OrderDirection.ASC

    def test_explicit_desc_direction(self) -> None:
        order = DomainOrder(field=DomainOrderField.CREATED_AT, direction=OrderDirection.DESC)
        assert order.direction == OrderDirection.DESC

    def test_round_trip(self) -> None:
        order = DomainOrder(field=DomainOrderField.MODIFIED_AT, direction=OrderDirection.DESC)
        json_data = order.model_dump_json()
        restored = DomainOrder.model_validate_json(json_data)
        assert restored.field == DomainOrderField.MODIFIED_AT
        assert restored.direction == OrderDirection.DESC


class TestSearchDomainsRequest:
    """Tests for SearchDomainsRequest model."""

    def test_defaults(self) -> None:
        req = SearchDomainsRequest()
        assert req.filter is None
        assert req.order is None
        assert req.offset == 0

    def test_limit_default_is_positive(self) -> None:
        req = SearchDomainsRequest()
        assert req.limit >= 1

    def test_limit_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchDomainsRequest(limit=0)

    def test_negative_offset_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchDomainsRequest(offset=-1)

    def test_with_filter_and_order(self) -> None:
        req = SearchDomainsRequest(
            filter=DomainFilter(is_active=True),
            order=[DomainOrder(field=DomainOrderField.NAME)],
            limit=5,
            offset=10,
        )
        assert req.filter is not None
        assert req.filter.is_active is True
        assert req.order is not None
        assert len(req.order) == 1
        assert req.limit == 5
        assert req.offset == 10

    def test_round_trip(self) -> None:
        req = SearchDomainsRequest(
            filter=DomainFilter(is_active=False),
            limit=15,
            offset=5,
        )
        json_data = req.model_dump_json()
        restored = SearchDomainsRequest.model_validate_json(json_data)
        assert restored.filter is not None
        assert restored.filter.is_active is False
        assert restored.limit == 15
        assert restored.offset == 5
