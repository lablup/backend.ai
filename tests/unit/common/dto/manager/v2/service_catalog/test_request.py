"""Tests for ai.backend.common.dto.manager.v2.service_catalog.request module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.dto.manager.v2.service_catalog.request import (
    CreateServiceCatalogInput,
    DeleteServiceCatalogInput,
    EndpointInput,
    HeartbeatInput,
    UpdateServiceCatalogInput,
)
from ai.backend.common.types import ServiceCatalogStatus


def _make_endpoint_input(**kwargs: object) -> EndpointInput:
    defaults: dict[str, Any] = {
        "role": "primary",
        "scope": "internal",
        "address": "192.168.1.100",
        "port": 8080,
        "protocol": "http",
    }
    defaults.update(kwargs)
    return EndpointInput(**defaults)


def _make_create_input(**kwargs: object) -> CreateServiceCatalogInput:
    defaults: dict[str, Any] = {
        "service_group": "my-group",
        "instance_id": "instance-001",
        "display_name": "My Service",
        "version": "1.0.0",
        "status": ServiceCatalogStatus.HEALTHY,
        "startup_time": datetime.now(tz=UTC),
    }
    defaults.update(kwargs)
    return CreateServiceCatalogInput(**defaults)


class TestEndpointInput:
    """Tests for EndpointInput model creation and validation."""

    def test_valid_creation(self) -> None:
        inp = _make_endpoint_input()
        assert inp.role == "primary"
        assert inp.scope == "internal"
        assert inp.address == "192.168.1.100"
        assert inp.port == 8080
        assert inp.protocol == "http"

    def test_metadata_defaults_to_none(self) -> None:
        inp = _make_endpoint_input()
        assert inp.metadata is None

    def test_with_metadata(self) -> None:
        inp = _make_endpoint_input(metadata={"region": "us-east"})
        assert inp.metadata == {"region": "us-east"}

    def test_port_min_is_1(self) -> None:
        with pytest.raises(ValidationError):
            _make_endpoint_input(port=0)

    def test_port_max_is_65535(self) -> None:
        with pytest.raises(ValidationError):
            _make_endpoint_input(port=65536)

    def test_port_at_min_is_valid(self) -> None:
        inp = _make_endpoint_input(port=1)
        assert inp.port == 1

    def test_port_at_max_is_valid(self) -> None:
        inp = _make_endpoint_input(port=65535)
        assert inp.port == 65535

    def test_role_max_length_32(self) -> None:
        with pytest.raises(ValidationError):
            _make_endpoint_input(role="r" * 33)

    def test_role_min_length_1(self) -> None:
        with pytest.raises(ValidationError):
            _make_endpoint_input(role="")

    def test_scope_max_length_32(self) -> None:
        with pytest.raises(ValidationError):
            _make_endpoint_input(scope="s" * 33)

    def test_address_max_length_256(self) -> None:
        with pytest.raises(ValidationError):
            _make_endpoint_input(address="a" * 257)

    def test_protocol_max_length_16(self) -> None:
        with pytest.raises(ValidationError):
            _make_endpoint_input(protocol="p" * 17)

    def test_round_trip(self) -> None:
        inp = _make_endpoint_input(port=9000, protocol="grpc", metadata={"key": "val"})
        json_str = inp.model_dump_json()
        restored = EndpointInput.model_validate_json(json_str)
        assert restored.port == 9000
        assert restored.protocol == "grpc"
        assert restored.metadata == {"key": "val"}


class TestCreateServiceCatalogInput:
    """Tests for CreateServiceCatalogInput model creation and validation."""

    def test_valid_creation_with_required_fields(self) -> None:
        inp = _make_create_input()
        assert inp.service_group == "my-group"
        assert inp.instance_id == "instance-001"
        assert inp.display_name == "My Service"
        assert inp.version == "1.0.0"
        assert inp.status == ServiceCatalogStatus.HEALTHY

    def test_display_name_whitespace_is_stripped(self) -> None:
        inp = _make_create_input(display_name="  My Service  ")
        assert inp.display_name == "My Service"

    def test_whitespace_only_display_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(display_name="   ")

    def test_empty_display_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(display_name="")

    def test_labels_defaults_to_empty_dict(self) -> None:
        inp = _make_create_input()
        assert inp.labels == {}

    def test_config_hash_defaults_to_empty_string(self) -> None:
        inp = _make_create_input()
        assert inp.config_hash == ""

    def test_endpoints_defaults_to_none(self) -> None:
        inp = _make_create_input()
        assert inp.endpoints is None

    def test_service_group_min_length_1(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(service_group="")

    def test_service_group_max_length_64(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(service_group="g" * 65)

    def test_instance_id_min_length_1(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(instance_id="")

    def test_instance_id_max_length_128(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(instance_id="i" * 129)

    def test_display_name_max_length_256(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(display_name="d" * 257)

    def test_version_min_length_1(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(version="")

    def test_version_max_length_64(self) -> None:
        with pytest.raises(ValidationError):
            _make_create_input(version="v" * 65)

    def test_with_labels(self) -> None:
        inp = _make_create_input(labels={"env": "prod", "team": "ml"})
        assert inp.labels == {"env": "prod", "team": "ml"}

    def test_with_endpoints(self) -> None:
        endpoint = _make_endpoint_input()
        inp = _make_create_input(endpoints=[endpoint])
        assert inp.endpoints is not None
        assert len(inp.endpoints) == 1

    def test_unhealthy_status(self) -> None:
        inp = _make_create_input(status=ServiceCatalogStatus.UNHEALTHY)
        assert inp.status == ServiceCatalogStatus.UNHEALTHY

    def test_deregistered_status(self) -> None:
        inp = _make_create_input(status=ServiceCatalogStatus.DEREGISTERED)
        assert inp.status == ServiceCatalogStatus.DEREGISTERED

    def test_round_trip(self) -> None:
        now = datetime.now(tz=UTC)
        inp = _make_create_input(startup_time=now, config_hash="abc123")
        json_str = inp.model_dump_json()
        restored = CreateServiceCatalogInput.model_validate_json(json_str)
        assert restored.service_group == "my-group"
        assert restored.display_name == "My Service"
        assert restored.config_hash == "abc123"
        assert restored.status == ServiceCatalogStatus.HEALTHY


class TestUpdateServiceCatalogInput:
    """Tests for UpdateServiceCatalogInput model creation and validation."""

    def test_all_none_fields_is_valid(self) -> None:
        inp = UpdateServiceCatalogInput(
            display_name=None,
            version=None,
            labels=None,
            status=None,
            config_hash=None,
        )
        assert inp.display_name is None
        assert inp.version is None
        assert inp.labels is None
        assert inp.status is None
        assert inp.config_hash is None

    def test_default_labels_is_sentinel(self) -> None:
        inp = UpdateServiceCatalogInput()
        assert inp.labels is SENTINEL
        assert isinstance(inp.labels, Sentinel)

    def test_explicit_sentinel_labels_signals_clear(self) -> None:
        inp = UpdateServiceCatalogInput(labels=SENTINEL)
        assert inp.labels is SENTINEL
        assert isinstance(inp.labels, Sentinel)

    def test_none_labels_means_no_change(self) -> None:
        inp = UpdateServiceCatalogInput(labels=None)
        assert inp.labels is None

    def test_dict_labels_update(self) -> None:
        inp = UpdateServiceCatalogInput(labels={"env": "staging"})
        assert inp.labels == {"env": "staging"}

    def test_display_name_whitespace_is_stripped(self) -> None:
        inp = UpdateServiceCatalogInput(display_name="  Updated Name  ")
        assert inp.display_name == "Updated Name"

    def test_whitespace_only_display_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateServiceCatalogInput(display_name="   ")

    def test_empty_display_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateServiceCatalogInput(display_name="")

    def test_version_update(self) -> None:
        inp = UpdateServiceCatalogInput(version="2.0.0")
        assert inp.version == "2.0.0"

    def test_status_update(self) -> None:
        inp = UpdateServiceCatalogInput(status=ServiceCatalogStatus.UNHEALTHY)
        assert inp.status == ServiceCatalogStatus.UNHEALTHY

    def test_config_hash_update(self) -> None:
        inp = UpdateServiceCatalogInput(config_hash="newHash123")
        assert inp.config_hash == "newHash123"

    def test_partial_update(self) -> None:
        inp = UpdateServiceCatalogInput(version="1.1.0")
        assert inp.version == "1.1.0"
        assert inp.display_name is None
        assert inp.status is None

    def test_round_trip_with_none_labels(self) -> None:
        inp = UpdateServiceCatalogInput(
            display_name="New Name", version=None, labels=None, status=None, config_hash=None
        )
        json_str = inp.model_dump_json()
        restored = UpdateServiceCatalogInput.model_validate_json(json_str)
        assert restored.display_name == "New Name"
        assert restored.labels is None


class TestDeleteServiceCatalogInput:
    """Tests for DeleteServiceCatalogInput model creation and validation."""

    def test_valid_creation_with_uuid(self) -> None:
        catalog_id = uuid.uuid4()
        inp = DeleteServiceCatalogInput(id=catalog_id)
        assert inp.id == catalog_id

    def test_valid_creation_from_uuid_string(self) -> None:
        catalog_id = uuid.uuid4()
        inp = DeleteServiceCatalogInput.model_validate({"id": str(catalog_id)})
        assert inp.id == catalog_id

    def test_invalid_uuid_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteServiceCatalogInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteServiceCatalogInput.model_validate({})

    def test_id_is_uuid_instance(self) -> None:
        inp = DeleteServiceCatalogInput(id=uuid.uuid4())
        assert isinstance(inp.id, uuid.UUID)

    def test_round_trip(self) -> None:
        catalog_id = uuid.uuid4()
        inp = DeleteServiceCatalogInput(id=catalog_id)
        json_str = inp.model_dump_json()
        restored = DeleteServiceCatalogInput.model_validate_json(json_str)
        assert restored.id == catalog_id


class TestHeartbeatInput:
    """Tests for HeartbeatInput model creation and validation."""

    def test_valid_creation_with_uuid(self) -> None:
        catalog_id = uuid.uuid4()
        inp = HeartbeatInput(id=catalog_id)
        assert inp.id == catalog_id

    def test_valid_creation_from_uuid_string(self) -> None:
        catalog_id = uuid.uuid4()
        inp = HeartbeatInput.model_validate({"id": str(catalog_id)})
        assert inp.id == catalog_id

    def test_invalid_uuid_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            HeartbeatInput.model_validate({"id": "bad-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            HeartbeatInput.model_validate({})

    def test_id_is_uuid_instance(self) -> None:
        inp = HeartbeatInput(id=uuid.uuid4())
        assert isinstance(inp.id, uuid.UUID)

    def test_round_trip(self) -> None:
        catalog_id = uuid.uuid4()
        inp = HeartbeatInput(id=catalog_id)
        json_str = inp.model_dump_json()
        restored = HeartbeatInput.model_validate_json(json_str)
        assert restored.id == catalog_id
