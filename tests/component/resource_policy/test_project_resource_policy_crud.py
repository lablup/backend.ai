"""Component tests for project resource policy v2 CRUD."""

from __future__ import annotations

import secrets

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    UpdateProjectResourcePolicyInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    CreateProjectResourcePolicyPayload,
)

from .conftest import ProjectResourcePolicyFactory


class TestProjectResourcePolicyCreate:
    """Tests for project resource policy creation."""

    async def test_s1_create_returns_correct_fields(
        self,
        admin_v2_registry: V2ClientRegistry,
        project_resource_policy_factory: ProjectResourcePolicyFactory,
    ) -> None:
        """S-1: Create project resource policy with all fields."""
        unique = secrets.token_hex(4)
        name = f"crud-prp-s1-{unique}"
        result = await project_resource_policy_factory(
            name=name,
            max_vfolder_count=20,
            max_quota_scope_size=0,
            max_network_count=10,
        )
        assert isinstance(result, CreateProjectResourcePolicyPayload)
        policy = result.project_resource_policy
        assert policy.name == name
        assert policy.max_vfolder_count == 20
        assert policy.max_network_count == 10

    async def test_s2_create_with_unlimited_networks(
        self,
        admin_v2_registry: V2ClientRegistry,
        project_resource_policy_factory: ProjectResourcePolicyFactory,
    ) -> None:
        """S-2: Create with max_network_count=-1 (unlimited)."""
        result = await project_resource_policy_factory(max_network_count=-1)
        assert result.project_resource_policy.max_network_count == -1


class TestProjectResourcePolicyGet:
    """Tests for project resource policy retrieval."""

    async def test_s1_get_by_name(
        self,
        admin_v2_registry: V2ClientRegistry,
        project_resource_policy_factory: ProjectResourcePolicyFactory,
    ) -> None:
        """S-1: Get policy by name."""
        created = await project_resource_policy_factory()
        name = created.project_resource_policy.name

        result = await admin_v2_registry.resource_policy.admin_get_project_resource_policy(name)
        assert result.name == name
        assert result.max_vfolder_count == created.project_resource_policy.max_vfolder_count


class TestProjectResourcePolicyUpdate:
    """Tests for project resource policy update."""

    async def test_s1_update_partial_fields(
        self,
        admin_v2_registry: V2ClientRegistry,
        project_resource_policy_factory: ProjectResourcePolicyFactory,
    ) -> None:
        """S-1: Update max_network_count, others unchanged."""
        created = await project_resource_policy_factory(max_network_count=3)
        name = created.project_resource_policy.name

        result = await admin_v2_registry.resource_policy.admin_update_project_resource_policy(
            name, UpdateProjectResourcePolicyInput(max_network_count=20)
        )
        assert result.project_resource_policy.max_network_count == 20
        assert (
            result.project_resource_policy.max_vfolder_count
            == created.project_resource_policy.max_vfolder_count
        )


class TestProjectResourcePolicyDelete:
    """Tests for project resource policy deletion."""

    async def test_s1_delete_by_name(
        self,
        admin_v2_registry: V2ClientRegistry,
        project_resource_policy_factory: ProjectResourcePolicyFactory,
    ) -> None:
        """S-1: Delete policy."""
        created = await project_resource_policy_factory()
        name = created.project_resource_policy.name

        result = await admin_v2_registry.resource_policy.admin_delete_project_resource_policy(name)
        assert result.name == name
