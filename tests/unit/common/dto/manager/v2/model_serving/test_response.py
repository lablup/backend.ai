"""Tests for ai.backend.common.dto.manager.v2.model_serving.response module."""

from __future__ import annotations

import uuid
from typing import Any

from ai.backend.common.dto.manager.v2.model_serving.response import (
    CompactServiceNode,
    CreateServicePayload,
    DeleteServicePayload,
    GenerateTokenPayload,
    ScaleServicePayload,
    ServiceNode,
    UpdateServicePayload,
)
from ai.backend.common.dto.manager.v2.model_serving.types import RouteInfoSummary
from ai.backend.common.types import RuntimeVariant


def _make_route_summary(**kwargs: object) -> RouteInfoSummary:
    defaults: dict[str, Any] = {
        "route_id": uuid.uuid4(),
        "session_id": None,
        "traffic_ratio": 1.0,
    }
    defaults.update(kwargs)
    return RouteInfoSummary(**defaults)


def _make_service_node(**kwargs: object) -> ServiceNode:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "name": "my-service",
        "replicas": 2,
        "active_route_count": 2,
        "service_endpoint": None,
        "is_public": False,
        "runtime_variant": RuntimeVariant("custom"),
        "model_id": None,
        "model_definition_path": None,
        "active_routes": [],
    }
    defaults.update(kwargs)
    return ServiceNode(**defaults)


class TestServiceNode:
    """Tests for ServiceNode model creation and serialization."""

    def test_creation_with_required_fields(self) -> None:
        service_id = uuid.uuid4()
        node = ServiceNode(
            id=service_id,
            name="my-service",
            replicas=2,
            active_route_count=2,
            is_public=False,
            runtime_variant=RuntimeVariant("custom"),
        )
        assert node.id == service_id
        assert node.name == "my-service"
        assert node.replicas == 2
        assert node.active_route_count == 2
        assert node.is_public is False
        assert node.runtime_variant == RuntimeVariant("custom")

    def test_service_endpoint_defaults_to_none(self) -> None:
        node = _make_service_node()
        assert node.service_endpoint is None

    def test_model_id_defaults_to_none(self) -> None:
        node = _make_service_node()
        assert node.model_id is None

    def test_model_definition_path_defaults_to_none(self) -> None:
        node = _make_service_node()
        assert node.model_definition_path is None

    def test_active_routes_defaults_to_empty_list(self) -> None:
        node = _make_service_node()
        assert node.active_routes == []

    def test_with_active_routes(self) -> None:
        route = _make_route_summary()
        node = _make_service_node(active_routes=[route])
        assert len(node.active_routes) == 1
        assert node.active_routes[0].traffic_ratio == 1.0

    def test_with_multiple_active_routes(self) -> None:
        routes = [
            _make_route_summary(traffic_ratio=0.5),
            _make_route_summary(traffic_ratio=0.5),
        ]
        node = _make_service_node(active_routes=routes)
        assert len(node.active_routes) == 2

    def test_is_public_true(self) -> None:
        node = _make_service_node(is_public=True)
        assert node.is_public is True

    def test_with_service_endpoint(self) -> None:
        node = _make_service_node(service_endpoint="https://service.example.com")
        assert node.service_endpoint == "https://service.example.com"

    def test_with_vllm_runtime_variant(self) -> None:
        node = _make_service_node(runtime_variant=RuntimeVariant("vllm"))
        assert node.runtime_variant == RuntimeVariant("vllm")

    def test_round_trip(self) -> None:
        service_id = uuid.uuid4()
        node = _make_service_node(id=service_id, name="test-svc")
        json_str = node.model_dump_json()
        restored = ServiceNode.model_validate_json(json_str)
        assert restored.id == service_id
        assert restored.name == "test-svc"
        assert restored.active_routes == []

    def test_round_trip_with_routes(self) -> None:
        service_id = uuid.uuid4()
        route_id = uuid.uuid4()
        session_id = uuid.uuid4()
        route = RouteInfoSummary(
            route_id=route_id,
            session_id=session_id,
            traffic_ratio=0.5,
        )
        node = _make_service_node(id=service_id, active_routes=[route])
        json_str = node.model_dump_json()
        restored = ServiceNode.model_validate_json(json_str)
        assert restored.id == service_id
        assert len(restored.active_routes) == 1
        assert restored.active_routes[0].route_id == route_id
        assert restored.active_routes[0].session_id == session_id


class TestCompactServiceNode:
    """Tests for CompactServiceNode model creation and serialization."""

    def test_creation_with_all_fields(self) -> None:
        service_id = uuid.uuid4()
        node = CompactServiceNode(
            id=service_id,
            name="my-service",
            replicas=2,
            active_route_count=2,
            service_endpoint=None,
            is_public=False,
        )
        assert node.id == service_id
        assert node.name == "my-service"
        assert node.replicas == 2
        assert node.active_route_count == 2
        assert node.service_endpoint is None
        assert node.is_public is False

    def test_service_endpoint_defaults_to_none(self) -> None:
        node = CompactServiceNode(
            id=uuid.uuid4(),
            name="svc",
            replicas=1,
            active_route_count=1,
            is_public=False,
        )
        assert node.service_endpoint is None

    def test_round_trip(self) -> None:
        service_id = uuid.uuid4()
        node = CompactServiceNode(
            id=service_id,
            name="compact-svc",
            replicas=3,
            active_route_count=3,
            service_endpoint="https://svc.example.com",
            is_public=True,
        )
        json_str = node.model_dump_json()
        restored = CompactServiceNode.model_validate_json(json_str)
        assert restored.id == service_id
        assert restored.name == "compact-svc"
        assert restored.replicas == 3
        assert restored.is_public is True


class TestCreateServicePayload:
    """Tests for CreateServicePayload model."""

    def test_creation_with_service_node(self) -> None:
        service_id = uuid.uuid4()
        node = _make_service_node(id=service_id)
        payload = CreateServicePayload(service=node)
        assert payload.service.id == service_id

    def test_service_name_accessible(self) -> None:
        node = _make_service_node(name="created-svc")
        payload = CreateServicePayload(service=node)
        assert payload.service.name == "created-svc"

    def test_round_trip(self) -> None:
        service_id = uuid.uuid4()
        node = _make_service_node(id=service_id)
        payload = CreateServicePayload(service=node)
        json_str = payload.model_dump_json()
        restored = CreateServicePayload.model_validate_json(json_str)
        assert restored.service.id == service_id


class TestUpdateServicePayload:
    """Tests for UpdateServicePayload model."""

    def test_creation_with_service_node(self) -> None:
        service_id = uuid.uuid4()
        node = _make_service_node(id=service_id)
        payload = UpdateServicePayload(service=node)
        assert payload.service.id == service_id

    def test_round_trip(self) -> None:
        service_id = uuid.uuid4()
        node = _make_service_node(id=service_id, name="updated-svc")
        payload = UpdateServicePayload(service=node)
        json_str = payload.model_dump_json()
        restored = UpdateServicePayload.model_validate_json(json_str)
        assert restored.service.id == service_id
        assert restored.service.name == "updated-svc"


class TestDeleteServicePayload:
    """Tests for DeleteServicePayload model."""

    def test_creation_with_success(self) -> None:
        service_id = uuid.uuid4()
        payload = DeleteServicePayload(id=service_id, success=True)
        assert payload.id == service_id
        assert payload.success is True

    def test_creation_with_failure(self) -> None:
        service_id = uuid.uuid4()
        payload = DeleteServicePayload(id=service_id, success=False)
        assert payload.success is False

    def test_id_is_uuid_instance(self) -> None:
        payload = DeleteServicePayload(id=uuid.uuid4(), success=True)
        assert isinstance(payload.id, uuid.UUID)

    def test_round_trip(self) -> None:
        service_id = uuid.uuid4()
        payload = DeleteServicePayload(id=service_id, success=True)
        json_str = payload.model_dump_json()
        restored = DeleteServicePayload.model_validate_json(json_str)
        assert restored.id == service_id
        assert restored.success is True


class TestScaleServicePayload:
    """Tests for ScaleServicePayload model."""

    def test_creation(self) -> None:
        payload = ScaleServicePayload(current_route_count=2, target_count=5)
        assert payload.current_route_count == 2
        assert payload.target_count == 5

    def test_scale_down(self) -> None:
        payload = ScaleServicePayload(current_route_count=5, target_count=2)
        assert payload.current_route_count == 5
        assert payload.target_count == 2

    def test_scale_to_zero(self) -> None:
        payload = ScaleServicePayload(current_route_count=3, target_count=0)
        assert payload.current_route_count == 3
        assert payload.target_count == 0

    def test_round_trip(self) -> None:
        payload = ScaleServicePayload(current_route_count=2, target_count=5)
        json_str = payload.model_dump_json()
        restored = ScaleServicePayload.model_validate_json(json_str)
        assert restored.current_route_count == 2
        assert restored.target_count == 5


class TestGenerateTokenPayload:
    """Tests for GenerateTokenPayload model."""

    def test_creation_with_token(self) -> None:
        payload = GenerateTokenPayload(token="abc123xyz")
        assert payload.token == "abc123xyz"

    def test_round_trip(self) -> None:
        payload = GenerateTokenPayload(token="my-secret-token-12345")
        json_str = payload.model_dump_json()
        restored = GenerateTokenPayload.model_validate_json(json_str)
        assert restored.token == "my-secret-token-12345"
