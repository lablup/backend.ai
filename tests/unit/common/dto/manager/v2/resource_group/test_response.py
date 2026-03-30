"""Tests for ai.backend.common.dto.manager.v2.resource_group.response module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ai.backend.common.dto.manager.v2.resource_group.response import (
    CreateResourceGroupPayload,
    DeleteResourceGroupPayload,
    ResourceGroupNode,
    UpdateResourceGroupPayload,
)


def _make_resource_group_node(name: str = "test-group") -> ResourceGroupNode:
    return ResourceGroupNode(
        id=uuid.uuid4(),
        name=name,
        domain_name="default",
        description="A test resource group",
        is_active=True,
        total_resource_slots={"cpu": "4", "mem": "8g"},
        allowed_vfolder_hosts={"default": "rw"},
        integration_id=None,
        resource_policy=None,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        modified_at=datetime(2024, 6, 1, tzinfo=UTC),
    )


class TestResourceGroupNode:
    """Tests for ResourceGroupNode model."""

    def test_valid_creation_with_all_fields(self) -> None:
        node = _make_resource_group_node()
        assert node.name == "test-group"
        assert node.domain_name == "default"
        assert node.is_active is True
        assert node.total_resource_slots == {"cpu": "4", "mem": "8g"}

    def test_valid_creation_with_optional_none(self) -> None:
        node = _make_resource_group_node()
        assert node.description == "A test resource group"
        assert node.integration_id is None
        assert node.resource_policy is None

    def test_serializes_correctly(self) -> None:
        node = _make_resource_group_node()
        data = node.model_dump()
        assert "id" in data
        assert "name" in data
        assert "domain_name" in data
        assert "total_resource_slots" in data
        assert "allowed_vfolder_hosts" in data

    def test_round_trip(self) -> None:
        node = _make_resource_group_node()
        json_data = node.model_dump_json()
        restored = ResourceGroupNode.model_validate_json(json_data)
        assert restored.name == node.name
        assert restored.domain_name == node.domain_name
        assert restored.is_active == node.is_active
        assert restored.id == node.id


class TestCreateResourceGroupPayload:
    """Tests for CreateResourceGroupPayload model."""

    def test_valid_creation(self) -> None:
        node = _make_resource_group_node()
        payload = CreateResourceGroupPayload(resource_group=node)
        assert payload.resource_group.name == "test-group"

    def test_round_trip(self) -> None:
        node = _make_resource_group_node()
        payload = CreateResourceGroupPayload(resource_group=node)
        json_data = payload.model_dump_json()
        restored = CreateResourceGroupPayload.model_validate_json(json_data)
        assert restored.resource_group.name == payload.resource_group.name


class TestUpdateResourceGroupPayload:
    """Tests for UpdateResourceGroupPayload model."""

    def test_valid_creation(self) -> None:
        node = _make_resource_group_node()
        payload = UpdateResourceGroupPayload(resource_group=node)
        assert payload.resource_group.name == "test-group"

    def test_round_trip(self) -> None:
        node = _make_resource_group_node()
        payload = UpdateResourceGroupPayload(resource_group=node)
        json_data = payload.model_dump_json()
        restored = UpdateResourceGroupPayload.model_validate_json(json_data)
        assert restored.resource_group.name == payload.resource_group.name


class TestDeleteResourceGroupPayload:
    """Tests for DeleteResourceGroupPayload model."""

    def test_valid_creation(self) -> None:
        group_id = uuid.uuid4()
        payload = DeleteResourceGroupPayload(id=group_id)
        assert payload.id == group_id

    def test_round_trip(self) -> None:
        group_id = uuid.uuid4()
        payload = DeleteResourceGroupPayload(id=group_id)
        json_data = payload.model_dump_json()
        restored = DeleteResourceGroupPayload.model_validate_json(json_data)
        assert restored.id == payload.id
