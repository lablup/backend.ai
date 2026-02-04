"""Unit tests for DomainV2 GraphQL types."""

from __future__ import annotations

from datetime import datetime

import pytest

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.api.gql.domain_v2.types import (
    DomainBasicInfoGQL,
    DomainLifecycleInfoGQL,
    DomainRegistryInfoGQL,
    DomainV2GQL,
)
from ai.backend.manager.data.domain.types import DomainData


class TestDomainV2GQL:
    """Tests for DomainV2GQL type conversions."""

    def test_from_data_basic_conversion(self) -> None:
        """Test basic DomainData to DomainV2GQL conversion."""
        data = DomainData(
            name="test-domain",
            description="Test domain description",
            is_active=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            modified_at=datetime(2024, 1, 2, 12, 0, 0),
            total_resource_slots=ResourceSlot(),
            allowed_vfolder_hosts=VFolderHostPermissionMap(),
            allowed_docker_registries=["docker.io", "ghcr.io"],
            dotfiles=b"",
            integration_id="integration-123",
        )

        domain_gql = DomainV2GQL.from_data(data)

        # Verify basic info
        assert domain_gql.basic_info.name == "test-domain"
        assert domain_gql.basic_info.description == "Test domain description"
        assert domain_gql.basic_info.integration_id == "integration-123"

        # Verify registry
        assert domain_gql.registry.allowed_docker_registries == ["docker.io", "ghcr.io"]

        # Verify lifecycle
        assert domain_gql.lifecycle.is_active is True
        assert domain_gql.lifecycle.created_at == datetime(2024, 1, 1, 12, 0, 0)
        assert domain_gql.lifecycle.modified_at == datetime(2024, 1, 2, 12, 0, 0)

    def test_from_data_primary_key_is_name(self) -> None:
        """Test that id field contains domain name, not UUID."""
        data = DomainData(
            name="my-domain",
            description=None,
            is_active=True,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            total_resource_slots=ResourceSlot(),
            allowed_vfolder_hosts=VFolderHostPermissionMap(),
            allowed_docker_registries=[],
            dotfiles=b"",
            integration_id=None,
        )

        domain_gql = DomainV2GQL.from_data(data)

        # ID should be the domain name
        assert str(domain_gql.id) == "my-domain"

    def test_from_data_empty_registries(self) -> None:
        """Test with empty allowed_docker_registries."""
        data = DomainData(
            name="test",
            description=None,
            is_active=True,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            total_resource_slots=ResourceSlot(),
            allowed_vfolder_hosts=VFolderHostPermissionMap(),
            allowed_docker_registries=[],
            dotfiles=b"",
            integration_id=None,
        )

        domain_gql = DomainV2GQL.from_data(data)
        assert len(domain_gql.registry.allowed_docker_registries) == 0

    def test_from_data_optional_fields(self) -> None:
        """Test handling of optional/nullable fields."""
        data = DomainData(
            name="minimal-domain",
            description=None,  # None description
            is_active=False,  # Inactive domain
            created_at=datetime.now(),
            modified_at=datetime.now(),
            total_resource_slots=ResourceSlot(),
            allowed_vfolder_hosts=VFolderHostPermissionMap(),
            allowed_docker_registries=[],
            dotfiles=b"",
            integration_id=None,  # None integration_id
        )

        domain_gql = DomainV2GQL.from_data(data)

        # Verify None values are preserved
        assert domain_gql.basic_info.description is None
        assert domain_gql.basic_info.integration_id is None
        assert domain_gql.lifecycle.is_active is False
