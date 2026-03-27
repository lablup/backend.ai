"""Tests for ai.backend.common.dto.manager.v2.service_catalog.response module."""

from __future__ import annotations

import json as json_module
import uuid
from datetime import UTC, datetime
from typing import Any

from ai.backend.common.dto.manager.v2.service_catalog.response import (
    CreateServiceCatalogPayload,
    DeleteServiceCatalogPayload,
    HeartbeatPayload,
    ServiceCatalogNode,
    UpdateServiceCatalogPayload,
)
from ai.backend.common.dto.manager.v2.service_catalog.types import EndpointInfo
from ai.backend.common.types import ServiceCatalogStatus


def _make_endpoint_info(**kwargs: object) -> EndpointInfo:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "role": "primary",
        "scope": "internal",
        "address": "192.168.1.100",
        "port": 8080,
        "protocol": "http",
        "metadata": None,
    }
    defaults.update(kwargs)
    return EndpointInfo(**defaults)


def _make_service_catalog_node(**kwargs: object) -> ServiceCatalogNode:
    now = datetime.now(tz=UTC)
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "service_group": "my-group",
        "instance_id": "instance-001",
        "display_name": "My Service",
        "version": "1.0.0",
        "labels": {},
        "status": ServiceCatalogStatus.HEALTHY,
        "startup_time": now,
        "registered_at": now,
        "last_heartbeat": now,
        "config_hash": "",
        "endpoints": [],
    }
    defaults.update(kwargs)
    return ServiceCatalogNode(**defaults)


class TestServiceCatalogNode:
    """Tests for ServiceCatalogNode model creation and serialization."""

    def test_creation_with_all_fields(self) -> None:
        catalog_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = ServiceCatalogNode(
            id=catalog_id,
            service_group="my-group",
            instance_id="instance-001",
            display_name="My Service",
            version="1.0.0",
            labels={"env": "prod"},
            status=ServiceCatalogStatus.HEALTHY,
            startup_time=now,
            registered_at=now,
            last_heartbeat=now,
            config_hash="abc123",
            endpoints=[],
        )
        assert node.id == catalog_id
        assert node.service_group == "my-group"
        assert node.instance_id == "instance-001"
        assert node.display_name == "My Service"
        assert node.version == "1.0.0"
        assert node.labels == {"env": "prod"}
        assert node.status == ServiceCatalogStatus.HEALTHY
        assert node.config_hash == "abc123"

    def test_endpoints_defaults_to_empty_list(self) -> None:
        node = _make_service_catalog_node()
        assert node.endpoints == []

    def test_labels_defaults_to_empty_dict(self) -> None:
        node = _make_service_catalog_node()
        assert node.labels == {}

    def test_with_single_endpoint(self) -> None:
        endpoint = _make_endpoint_info(role="primary", port=8080)
        node = _make_service_catalog_node(endpoints=[endpoint])
        assert len(node.endpoints) == 1
        assert node.endpoints[0].role == "primary"
        assert node.endpoints[0].port == 8080

    def test_with_multiple_endpoints(self) -> None:
        endpoints = [
            _make_endpoint_info(role="primary", port=8080),
            _make_endpoint_info(role="secondary", port=8081),
        ]
        node = _make_service_catalog_node(endpoints=endpoints)
        assert len(node.endpoints) == 2
        assert node.endpoints[0].role == "primary"
        assert node.endpoints[1].role == "secondary"

    def test_with_labels(self) -> None:
        node = _make_service_catalog_node(labels={"team": "ml", "env": "staging"})
        assert node.labels["team"] == "ml"
        assert node.labels["env"] == "staging"

    def test_unhealthy_status(self) -> None:
        node = _make_service_catalog_node(status=ServiceCatalogStatus.UNHEALTHY)
        assert node.status == ServiceCatalogStatus.UNHEALTHY

    def test_deregistered_status(self) -> None:
        node = _make_service_catalog_node(status=ServiceCatalogStatus.DEREGISTERED)
        assert node.status == ServiceCatalogStatus.DEREGISTERED

    def test_round_trip(self) -> None:
        catalog_id = uuid.uuid4()
        node = _make_service_catalog_node(id=catalog_id, config_hash="deadbeef")
        json_str = node.model_dump_json()
        restored = ServiceCatalogNode.model_validate_json(json_str)
        assert restored.id == catalog_id
        assert restored.service_group == "my-group"
        assert restored.config_hash == "deadbeef"
        assert restored.endpoints == []

    def test_round_trip_with_endpoints(self) -> None:
        catalog_id = uuid.uuid4()
        endpoint_id = uuid.uuid4()
        endpoint = _make_endpoint_info(id=endpoint_id, role="primary", port=9090)
        node = _make_service_catalog_node(id=catalog_id, endpoints=[endpoint])
        json_str = node.model_dump_json()
        restored = ServiceCatalogNode.model_validate_json(json_str)
        assert restored.id == catalog_id
        assert len(restored.endpoints) == 1
        assert restored.endpoints[0].id == endpoint_id
        assert restored.endpoints[0].role == "primary"
        assert restored.endpoints[0].port == 9090

    def test_round_trip_with_labels(self) -> None:
        node = _make_service_catalog_node(labels={"key": "value", "count": "42"})
        json_str = node.model_dump_json()
        restored = ServiceCatalogNode.model_validate_json(json_str)
        assert restored.labels == {"key": "value", "count": "42"}

    def test_status_serialized_as_string(self) -> None:
        node = _make_service_catalog_node(status=ServiceCatalogStatus.HEALTHY)
        data = json_module.loads(node.model_dump_json())
        assert isinstance(data["status"], str)


class TestCreateServiceCatalogPayload:
    """Tests for CreateServiceCatalogPayload model."""

    def test_creation_with_service_node(self) -> None:
        catalog_id = uuid.uuid4()
        node = _make_service_catalog_node(id=catalog_id)
        payload = CreateServiceCatalogPayload(service=node)
        assert payload.service.id == catalog_id

    def test_service_display_name_accessible(self) -> None:
        node = _make_service_catalog_node(display_name="Created Service")
        payload = CreateServiceCatalogPayload(service=node)
        assert payload.service.display_name == "Created Service"

    def test_round_trip(self) -> None:
        catalog_id = uuid.uuid4()
        node = _make_service_catalog_node(id=catalog_id)
        payload = CreateServiceCatalogPayload(service=node)
        json_str = payload.model_dump_json()
        restored = CreateServiceCatalogPayload.model_validate_json(json_str)
        assert restored.service.id == catalog_id

    def test_nested_endpoints_in_payload(self) -> None:
        endpoint = _make_endpoint_info(role="primary")
        node = _make_service_catalog_node(endpoints=[endpoint])
        payload = CreateServiceCatalogPayload(service=node)
        assert len(payload.service.endpoints) == 1
        assert payload.service.endpoints[0].role == "primary"


class TestUpdateServiceCatalogPayload:
    """Tests for UpdateServiceCatalogPayload model."""

    def test_creation_with_service_node(self) -> None:
        catalog_id = uuid.uuid4()
        node = _make_service_catalog_node(id=catalog_id)
        payload = UpdateServiceCatalogPayload(service=node)
        assert payload.service.id == catalog_id

    def test_round_trip(self) -> None:
        catalog_id = uuid.uuid4()
        node = _make_service_catalog_node(id=catalog_id, display_name="Updated Service")
        payload = UpdateServiceCatalogPayload(service=node)
        json_str = payload.model_dump_json()
        restored = UpdateServiceCatalogPayload.model_validate_json(json_str)
        assert restored.service.id == catalog_id
        assert restored.service.display_name == "Updated Service"


class TestDeleteServiceCatalogPayload:
    """Tests for DeleteServiceCatalogPayload model."""

    def test_creation_with_uuid(self) -> None:
        catalog_id = uuid.uuid4()
        payload = DeleteServiceCatalogPayload(id=catalog_id)
        assert payload.id == catalog_id

    def test_id_is_uuid_instance(self) -> None:
        payload = DeleteServiceCatalogPayload(id=uuid.uuid4())
        assert isinstance(payload.id, uuid.UUID)

    def test_creation_from_uuid_string(self) -> None:
        catalog_id = uuid.uuid4()
        payload = DeleteServiceCatalogPayload.model_validate({"id": str(catalog_id)})
        assert payload.id == catalog_id

    def test_round_trip(self) -> None:
        catalog_id = uuid.uuid4()
        payload = DeleteServiceCatalogPayload(id=catalog_id)
        json_str = payload.model_dump_json()
        restored = DeleteServiceCatalogPayload.model_validate_json(json_str)
        assert restored.id == catalog_id


class TestHeartbeatPayload:
    """Tests for HeartbeatPayload model."""

    def test_creation_with_success(self) -> None:
        now = datetime.now(tz=UTC)
        payload = HeartbeatPayload(success=True, last_heartbeat=now)
        assert payload.success is True
        assert payload.last_heartbeat == now

    def test_creation_with_failure(self) -> None:
        now = datetime.now(tz=UTC)
        payload = HeartbeatPayload(success=False, last_heartbeat=now)
        assert payload.success is False

    def test_round_trip(self) -> None:
        now = datetime.now(tz=UTC)
        payload = HeartbeatPayload(success=True, last_heartbeat=now)
        json_str = payload.model_dump_json()
        restored = HeartbeatPayload.model_validate_json(json_str)
        assert restored.success is True
        assert restored.last_heartbeat is not None
