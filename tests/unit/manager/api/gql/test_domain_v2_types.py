"""Unit tests for DomainV2 GraphQL types."""

from __future__ import annotations

from datetime import UTC, datetime

from ai.backend.common.dto.manager.v2.domain.response import (
    DomainBasicInfo,
    DomainLifecycleInfo,
    DomainNode,
    DomainRegistryInfo,
)
from ai.backend.manager.api.gql.domain_v2.types import (
    DomainV2GQL,
)


def _make_domain_node(
    *,
    name: str = "test-domain",
    description: str | None = "Test domain description",
    integration_name: str | None = "integration-123",
    allowed_docker_registries: list[str] | None = None,
    is_active: bool = True,
    created_at: datetime | None = None,
    modified_at: datetime | None = None,
) -> DomainNode:
    now = datetime.now(tz=UTC)
    return DomainNode(
        id=name,
        basic_info=DomainBasicInfo(
            name=name,
            description=description,
            integration_name=integration_name,
        ),
        registry=DomainRegistryInfo(
            allowed_docker_registries=allowed_docker_registries or [],
        ),
        lifecycle=DomainLifecycleInfo(
            is_active=is_active,
            created_at=created_at or now,
            modified_at=modified_at or now,
        ),
    )


class TestDomainV2GQL:
    """Tests for DomainV2GQL type conversions."""

    def test_from_pydantic_basic_conversion(self) -> None:
        """Test basic DomainNode to DomainV2GQL conversion."""
        created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        modified = datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC)
        dto = _make_domain_node(
            name="test-domain",
            description="Test domain description",
            integration_name="integration-123",
            allowed_docker_registries=["docker.io", "ghcr.io"],
            is_active=True,
            created_at=created,
            modified_at=modified,
        )

        domain_gql = DomainV2GQL.from_pydantic(dto)

        # Verify basic info
        assert domain_gql.basic_info.name == "test-domain"
        assert domain_gql.basic_info.description == "Test domain description"
        assert domain_gql.basic_info.integration_name == "integration-123"

        # Verify registry
        assert domain_gql.registry.allowed_docker_registries == ["docker.io", "ghcr.io"]

        # Verify lifecycle
        assert domain_gql.lifecycle.is_active is True
        assert domain_gql.lifecycle.created_at == created
        assert domain_gql.lifecycle.modified_at == modified

    def test_from_pydantic_primary_key_is_name(self) -> None:
        """Test that id field contains domain name, not UUID."""
        dto = _make_domain_node(name="my-domain")

        domain_gql = DomainV2GQL.from_pydantic(dto)

        # ID should be the domain name
        assert str(domain_gql.id) == "my-domain"

    def test_from_pydantic_empty_registries(self) -> None:
        """Test with empty allowed_docker_registries."""
        dto = _make_domain_node(allowed_docker_registries=[])

        domain_gql = DomainV2GQL.from_pydantic(dto)
        assert len(domain_gql.registry.allowed_docker_registries) == 0

    def test_from_pydantic_optional_fields(self) -> None:
        """Test handling of optional/nullable fields."""
        dto = _make_domain_node(
            name="minimal-domain",
            description=None,
            integration_name=None,
            is_active=False,
        )

        domain_gql = DomainV2GQL.from_pydantic(dto)

        # Verify None values are preserved
        assert domain_gql.basic_info.description is None
        assert domain_gql.basic_info.integration_name is None
        assert domain_gql.lifecycle.is_active is False
