"""Tests for ai.backend.common.dto.manager.v2.domain.response module."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.domain.response import (
    DeleteDomainPayload,
    DomainBasicInfo,
    DomainLifecycleInfo,
    DomainNode,
    DomainPayload,
    DomainRegistryInfo,
    PurgeDomainPayload,
    SearchDomainsPayload,
)


def make_domain_node(name: str = "test-domain") -> DomainNode:
    """Helper to create a valid DomainNode for testing."""
    now = datetime.now(tz=UTC)
    return DomainNode(
        id=name,
        basic_info=DomainBasicInfo(
            name=name,
            description="Test domain",
            integration_name=None,
        ),
        registry=DomainRegistryInfo(
            allowed_docker_registries=["registry.example.com"],
        ),
        lifecycle=DomainLifecycleInfo(
            is_active=True,
            created_at=now,
            modified_at=now,
        ),
    )


class TestDomainBasicInfo:
    """Tests for DomainBasicInfo sub-model."""

    def test_creation_with_required_fields(self) -> None:
        info = DomainBasicInfo(name="test")
        assert info.name == "test"
        assert info.description is None
        assert info.integration_name is None

    def test_creation_with_all_fields(self) -> None:
        info = DomainBasicInfo(
            name="production",
            description="Production domain",
            integration_name="ext-123",
        )
        assert info.description == "Production domain"
        assert info.integration_name == "ext-123"

    def test_round_trip(self) -> None:
        info = DomainBasicInfo(name="domain", description="Desc", integration_name="id-1")
        json_data = info.model_dump_json()
        restored = DomainBasicInfo.model_validate_json(json_data)
        assert restored.name == "domain"
        assert restored.description == "Desc"
        assert restored.integration_name == "id-1"


class TestDomainRegistryInfo:
    """Tests for DomainRegistryInfo sub-model."""

    def test_empty_registries(self) -> None:
        info = DomainRegistryInfo(allowed_docker_registries=[])
        assert info.allowed_docker_registries == []

    def test_with_registries(self) -> None:
        info = DomainRegistryInfo(
            allowed_docker_registries=["registry1.example.com", "registry2.example.com"]
        )
        assert len(info.allowed_docker_registries) == 2
        assert "registry1.example.com" in info.allowed_docker_registries

    def test_round_trip(self) -> None:
        info = DomainRegistryInfo(allowed_docker_registries=["reg.example.com"])
        json_data = info.model_dump_json()
        restored = DomainRegistryInfo.model_validate_json(json_data)
        assert restored.allowed_docker_registries == ["reg.example.com"]


class TestDomainLifecycleInfo:
    """Tests for DomainLifecycleInfo sub-model."""

    def test_creation_with_all_fields(self) -> None:
        now = datetime.now(tz=UTC)
        info = DomainLifecycleInfo(is_active=True, created_at=now, modified_at=now)
        assert info.is_active is True
        assert info.created_at == now

    def test_inactive_domain(self) -> None:
        now = datetime.now(tz=UTC)
        info = DomainLifecycleInfo(is_active=False, created_at=now, modified_at=now)
        assert info.is_active is False

    def test_round_trip(self) -> None:
        now = datetime.now(tz=UTC)
        info = DomainLifecycleInfo(is_active=True, created_at=now, modified_at=now)
        json_data = info.model_dump_json()
        restored = DomainLifecycleInfo.model_validate_json(json_data)
        assert restored.is_active is True
        assert restored.created_at is not None


class TestDomainNode:
    """Tests for DomainNode model with nested sub-models."""

    def test_creation_with_all_nested_groups(self) -> None:
        node = make_domain_node("my-domain")
        assert node.id == "my-domain"
        assert node.basic_info.name == "my-domain"
        assert node.registry.allowed_docker_registries == ["registry.example.com"]
        assert node.lifecycle.is_active is True

    def test_id_is_string(self) -> None:
        node = make_domain_node("test")
        assert isinstance(node.id, str)

    def test_nested_basic_info(self) -> None:
        node = make_domain_node("prod")
        assert node.basic_info.name == "prod"
        assert node.basic_info.description == "Test domain"
        assert node.basic_info.integration_name is None

    def test_nested_registry_info(self) -> None:
        node = make_domain_node()
        assert len(node.registry.allowed_docker_registries) == 1

    def test_nested_lifecycle_info(self) -> None:
        node = make_domain_node()
        assert node.lifecycle.is_active is True
        assert node.lifecycle.created_at is not None

    def test_round_trip_serialization(self) -> None:
        node = make_domain_node("serialized-domain")
        json_str = node.model_dump_json()
        restored = DomainNode.model_validate_json(json_str)
        assert restored.id == "serialized-domain"
        assert restored.basic_info.name == "serialized-domain"
        assert restored.lifecycle.is_active is True

    def test_serialized_json_has_nested_structure(self) -> None:
        node = make_domain_node()
        data = json.loads(node.model_dump_json())
        assert "basic_info" in data
        assert "registry" in data
        assert "lifecycle" in data
        assert "name" in data["basic_info"]
        assert "allowed_docker_registries" in data["registry"]


class TestDomainPayload:
    """Tests for DomainPayload model."""

    def test_creation_with_domain_node(self) -> None:
        node = make_domain_node("test")
        payload = DomainPayload(domain=node)
        assert payload.domain.id == "test"

    def test_round_trip(self) -> None:
        node = make_domain_node("production")
        payload = DomainPayload(domain=node)
        json_str = payload.model_dump_json()
        restored = DomainPayload.model_validate_json(json_str)
        assert restored.domain.id == "production"
        assert restored.domain.basic_info.name == "production"


class TestSearchDomainsPayload:
    """Tests for SearchDomainsPayload model."""

    def test_empty_items(self) -> None:
        payload = SearchDomainsPayload(
            items=[],
            pagination=PaginationInfo(total=0, offset=0, limit=20),
        )
        assert payload.items == []
        assert payload.pagination.total == 0

    def test_with_items(self) -> None:
        nodes = [make_domain_node("domain-1"), make_domain_node("domain-2")]
        payload = SearchDomainsPayload(
            items=nodes,
            pagination=PaginationInfo(total=2, offset=0, limit=10),
        )
        assert len(payload.items) == 2
        assert payload.pagination.total == 2

    def test_round_trip(self) -> None:
        node = make_domain_node("round-trip-domain")
        payload = SearchDomainsPayload(
            items=[node],
            pagination=PaginationInfo(total=1, offset=0, limit=10),
        )
        json_str = payload.model_dump_json()
        restored = SearchDomainsPayload.model_validate_json(json_str)
        assert len(restored.items) == 1
        assert restored.items[0].id == "round-trip-domain"
        assert restored.pagination.total == 1


class TestDeleteDomainPayload:
    """Tests for DeleteDomainPayload model."""

    def test_deleted_true(self) -> None:
        payload = DeleteDomainPayload(deleted=True)
        assert payload.deleted is True

    def test_deleted_false(self) -> None:
        payload = DeleteDomainPayload(deleted=False)
        assert payload.deleted is False

    def test_round_trip(self) -> None:
        payload = DeleteDomainPayload(deleted=True)
        json_str = payload.model_dump_json()
        restored = DeleteDomainPayload.model_validate_json(json_str)
        assert restored.deleted is True


class TestPurgeDomainPayload:
    """Tests for PurgeDomainPayload model."""

    def test_purged_true(self) -> None:
        payload = PurgeDomainPayload(purged=True)
        assert payload.purged is True

    def test_purged_false(self) -> None:
        payload = PurgeDomainPayload(purged=False)
        assert payload.purged is False

    def test_round_trip(self) -> None:
        payload = PurgeDomainPayload(purged=False)
        json_str = payload.model_dump_json()
        restored = PurgeDomainPayload.model_validate_json(json_str)
        assert restored.purged is False
