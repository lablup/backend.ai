"""Tests for ai.backend.common.dto.manager.v2.container_registry.response module."""

from __future__ import annotations

import json
import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.container_registry.response import (
    ContainerRegistryNode,
    CreateContainerRegistryPayload,
    DeleteContainerRegistryPayload,
    ListContainerRegistriesPayload,
    UpdateContainerRegistryPayload,
)
from ai.backend.common.dto.manager.v2.container_registry.types import ContainerRegistryType


def _make_registry_node(
    registry_type: ContainerRegistryType = ContainerRegistryType.DOCKER,
) -> ContainerRegistryNode:
    return ContainerRegistryNode(
        id=uuid.uuid4(),
        url="https://registry.example.com",
        registry_name="test-registry",
        type=registry_type,
    )


class TestContainerRegistryNode:
    """Tests for ContainerRegistryNode model creation."""

    def test_basic_creation(self) -> None:
        node = _make_registry_node()
        assert node.url == "https://registry.example.com"
        assert node.registry_name == "test-registry"
        assert node.type == ContainerRegistryType.DOCKER

    def test_optional_fields_default_to_none(self) -> None:
        node = _make_registry_node()
        assert node.project is None
        assert node.username is None
        assert node.ssl_verify is None
        assert node.is_global is None
        assert node.extra is None

    def test_has_no_password_field(self) -> None:
        """Verify password field is not present in ContainerRegistryNode."""
        node = _make_registry_node()
        data = node.model_dump()
        assert "password" not in data

    def test_with_optional_fields(self) -> None:
        node = ContainerRegistryNode(
            id=uuid.uuid4(),
            url="https://harbor.example.com",
            registry_name="harbor-reg",
            type=ContainerRegistryType.HARBOR,
            project="myproject",
            username="admin",
            ssl_verify=True,
            is_global=True,
        )
        assert node.project == "myproject"
        assert node.username == "admin"
        assert node.ssl_verify is True
        assert node.is_global is True

    def test_with_extra_metadata(self) -> None:
        node = ContainerRegistryNode(
            id=uuid.uuid4(),
            url="https://registry.example.com",
            registry_name="extra-reg",
            type=ContainerRegistryType.DOCKER,
            extra={"key": "value", "num": 42},
        )
        assert node.extra is not None
        assert node.extra["key"] == "value"

    def test_harbor2_type(self) -> None:
        node = _make_registry_node(registry_type=ContainerRegistryType.HARBOR2)
        assert node.type == ContainerRegistryType.HARBOR2

    def test_github_type(self) -> None:
        node = _make_registry_node(registry_type=ContainerRegistryType.GITHUB)
        assert node.type == ContainerRegistryType.GITHUB

    def test_gitlab_type(self) -> None:
        node = _make_registry_node(registry_type=ContainerRegistryType.GITLAB)
        assert node.type == ContainerRegistryType.GITLAB

    def test_json_contains_type_string(self) -> None:
        node = _make_registry_node()
        parsed = json.loads(node.model_dump_json())
        assert parsed["type"] == "docker"

    def test_serialization_round_trip(self) -> None:
        node = ContainerRegistryNode(
            id=uuid.uuid4(),
            url="https://registry.example.com",
            registry_name="my-reg",
            type=ContainerRegistryType.HARBOR,
            project="proj",
            username="user",
            ssl_verify=False,
            is_global=True,
        )
        json_str = node.model_dump_json()
        restored = ContainerRegistryNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.url == node.url
        assert restored.registry_name == node.registry_name
        assert restored.type == ContainerRegistryType.HARBOR
        assert restored.project == "proj"
        assert restored.username == "user"
        assert restored.ssl_verify is False
        assert restored.is_global is True


class TestCreateContainerRegistryPayload:
    """Tests for CreateContainerRegistryPayload model."""

    def test_creation_with_registry_node(self) -> None:
        node = _make_registry_node()
        payload = CreateContainerRegistryPayload(registry=node)
        assert payload.registry.registry_name == "test-registry"
        assert payload.registry.type == ContainerRegistryType.DOCKER

    def test_registry_id_accessible_via_payload(self) -> None:
        node = _make_registry_node()
        payload = CreateContainerRegistryPayload(registry=node)
        assert payload.registry.id == node.id

    def test_round_trip_serialization(self) -> None:
        node = _make_registry_node()
        payload = CreateContainerRegistryPayload(registry=node)
        json_str = payload.model_dump_json()
        restored = CreateContainerRegistryPayload.model_validate_json(json_str)
        assert restored.registry.id == node.id
        assert restored.registry.registry_name == node.registry_name
        assert restored.registry.type == ContainerRegistryType.DOCKER

    def test_no_password_in_payload(self) -> None:
        node = _make_registry_node()
        payload = CreateContainerRegistryPayload(registry=node)
        data = payload.model_dump()
        assert "password" not in data["registry"]


class TestUpdateContainerRegistryPayload:
    """Tests for UpdateContainerRegistryPayload model."""

    def test_creation_with_registry_node(self) -> None:
        node = ContainerRegistryNode(
            id=uuid.uuid4(),
            url="https://updated.example.com",
            registry_name="updated-registry",
            type=ContainerRegistryType.HARBOR,
        )
        payload = UpdateContainerRegistryPayload(registry=node)
        assert payload.registry.url == "https://updated.example.com"
        assert payload.registry.type == ContainerRegistryType.HARBOR

    def test_round_trip_serialization(self) -> None:
        node = _make_registry_node()
        payload = UpdateContainerRegistryPayload(registry=node)
        json_str = payload.model_dump_json()
        restored = UpdateContainerRegistryPayload.model_validate_json(json_str)
        assert restored.registry.id == node.id


class TestDeleteContainerRegistryPayload:
    """Tests for DeleteContainerRegistryPayload model."""

    def test_creation_with_uuid(self) -> None:
        reg_id = uuid.uuid4()
        payload = DeleteContainerRegistryPayload(id=reg_id)
        assert payload.id == reg_id

    def test_id_is_uuid_instance(self) -> None:
        reg_id = uuid.uuid4()
        payload = DeleteContainerRegistryPayload(id=reg_id)
        assert isinstance(payload.id, uuid.UUID)

    def test_creation_from_uuid_string(self) -> None:
        reg_id = uuid.uuid4()
        payload = DeleteContainerRegistryPayload.model_validate({"id": str(reg_id)})
        assert payload.id == reg_id

    def test_invalid_uuid_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteContainerRegistryPayload.model_validate({"id": "not-a-uuid"})

    def test_round_trip_serialization(self) -> None:
        reg_id = uuid.uuid4()
        payload = DeleteContainerRegistryPayload(id=reg_id)
        json_str = payload.model_dump_json()
        restored = DeleteContainerRegistryPayload.model_validate_json(json_str)
        assert restored.id == reg_id


class TestListContainerRegistriesPayload:
    """Tests for ListContainerRegistriesPayload model."""

    def test_creation_with_items(self) -> None:
        nodes = [_make_registry_node(), _make_registry_node(ContainerRegistryType.HARBOR)]
        payload = ListContainerRegistriesPayload(items=nodes)
        assert len(payload.items) == 2

    def test_empty_items_list(self) -> None:
        payload = ListContainerRegistriesPayload(items=[])
        assert payload.items == []

    def test_items_no_password_field(self) -> None:
        nodes = [_make_registry_node()]
        payload = ListContainerRegistriesPayload(items=nodes)
        data = payload.model_dump()
        assert "password" not in data["items"][0]

    def test_round_trip_serialization(self) -> None:
        nodes = [
            _make_registry_node(),
            _make_registry_node(ContainerRegistryType.GITLAB),
        ]
        payload = ListContainerRegistriesPayload(items=nodes)
        json_str = payload.model_dump_json()
        restored = ListContainerRegistriesPayload.model_validate_json(json_str)
        assert len(restored.items) == 2
        assert restored.items[0].id == nodes[0].id
        assert restored.items[1].type == ContainerRegistryType.GITLAB

    def test_json_structure(self) -> None:
        node = _make_registry_node()
        payload = ListContainerRegistriesPayload(items=[node])
        parsed = json.loads(payload.model_dump_json())
        assert "items" in parsed
        assert isinstance(parsed["items"], list)
        assert len(parsed["items"]) == 1
        assert parsed["items"][0]["type"] == "docker"
