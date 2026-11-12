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
from ai.backend.common.types import ServiceCatalogStatus


def _make_service_catalog_node(**kwargs: object) -> ServiceCatalogNode:
    now = datetime.now(tz=UTC)
    catalog_id = uuid.uuid4()
    defaults: dict[str, Any] = {
        "id": catalog_id,
        "entity_id": catalog_id,
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
            entity_id=catalog_id,
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
        )
        assert node.id == catalog_id
        assert node.service_group == "my-group"
        assert node.instance_id == "instance-001"
        assert node.display_name == "My Service"
        assert node.version == "1.0.0"
        assert node.labels == {"env": "prod"}
        assert node.status == ServiceCatalogStatus.HEALTHY
        assert node.config_hash == "abc123"

    def test_labels_defaults_to_empty_dict(self) -> None:
        node = _make_service_catalog_node()
        assert node.labels == {}

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
