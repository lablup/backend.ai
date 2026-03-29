"""Component tests for resource group allow/disallow REST v2 API."""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.resource_group.request import (
    UpdateAllowedDomainsForResourceGroupInput,
    UpdateAllowedProjectsForResourceGroupInput,
    UpdateAllowedResourceGroupsForDomainInput,
    UpdateAllowedResourceGroupsForProjectInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    AllowedDomainsPayload,
    AllowedProjectsPayload,
    AllowedResourceGroupsPayload,
)
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.scaling_group.row import ScalingGroupOpts, ScalingGroupRow


@pytest.fixture()
async def clean_domain_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[str]:
    """Create a domain with no pre-existing scaling group associations."""
    domain_name = f"clean-domain-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(domains).values(
                name=domain_name,
                description=f"Clean test domain {domain_name}",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
            )
        )
    yield domain_name
    async with db_engine.begin() as conn:
        await conn.execute(domains.delete().where(domains.c.name == domain_name))


@pytest.fixture()
async def extra_scaling_group(
    db_engine: SAEngine,
) -> AsyncIterator[str]:
    """Create an extra scaling group for allow/disallow tests."""
    name = f"test-sg-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ScalingGroupRow.__table__).values(
                name=name,
                description="Test scaling group for allow/disallow",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
        )
    yield name
    async with db_engine.begin() as conn:
        await conn.execute(
            ScalingGroupRow.__table__.delete().where(ScalingGroupRow.__table__.c.name == name)
        )


@pytest.fixture()
async def second_scaling_group(
    db_engine: SAEngine,
) -> AsyncIterator[str]:
    """Create a second scaling group for multi-allow tests."""
    name = f"test-sg2-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ScalingGroupRow.__table__).values(
                name=name,
                description="Second test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
        )
    yield name
    async with db_engine.begin() as conn:
        await conn.execute(
            ScalingGroupRow.__table__.delete().where(ScalingGroupRow.__table__.c.name == name)
        )


class TestAllowedResourceGroupsForDomain:
    """Tests for domain → resource group allow/disallow."""

    async def test_get_empty_allowed_list(
        self,
        admin_v2_registry: V2ClientRegistry,
        clean_domain_fixture: str,
    ) -> None:
        """Initially, a domain has no allowed resource groups."""
        result = await admin_v2_registry.resource_group.get_allowed_resource_groups_for_domain(
            clean_domain_fixture
        )
        assert isinstance(result, AllowedResourceGroupsPayload)
        assert result.items == []

    async def test_add_and_get_allowed(
        self,
        admin_v2_registry: V2ClientRegistry,
        domain_fixture: str,
        extra_scaling_group: str,
    ) -> None:
        """Allow a resource group for a domain, then verify it's listed."""
        result = await admin_v2_registry.resource_group.update_allowed_resource_groups_for_domain(
            domain_fixture,
            UpdateAllowedResourceGroupsForDomainInput(
                domain_name=domain_fixture,
                add=[extra_scaling_group],
            ),
        )
        assert isinstance(result, AllowedResourceGroupsPayload)
        assert extra_scaling_group in result.items

    async def test_add_and_remove_atomically(
        self,
        admin_v2_registry: V2ClientRegistry,
        domain_fixture: str,
        extra_scaling_group: str,
        second_scaling_group: str,
    ) -> None:
        """Add one and remove another in a single request."""
        # First, allow extra
        await admin_v2_registry.resource_group.update_allowed_resource_groups_for_domain(
            domain_fixture,
            UpdateAllowedResourceGroupsForDomainInput(
                domain_name=domain_fixture,
                add=[extra_scaling_group, second_scaling_group],
            ),
        )
        # Then remove extra, verify second remains
        result = await admin_v2_registry.resource_group.update_allowed_resource_groups_for_domain(
            domain_fixture,
            UpdateAllowedResourceGroupsForDomainInput(
                domain_name=domain_fixture,
                add=[],
                remove=[extra_scaling_group],
            ),
        )
        assert extra_scaling_group not in result.items
        assert second_scaling_group in result.items

    async def test_idempotent_add(
        self,
        admin_v2_registry: V2ClientRegistry,
        domain_fixture: str,
        extra_scaling_group: str,
    ) -> None:
        """Adding the same resource group twice should not error."""
        await admin_v2_registry.resource_group.update_allowed_resource_groups_for_domain(
            domain_fixture,
            UpdateAllowedResourceGroupsForDomainInput(
                domain_name=domain_fixture,
                add=[extra_scaling_group],
            ),
        )
        result = await admin_v2_registry.resource_group.update_allowed_resource_groups_for_domain(
            domain_fixture,
            UpdateAllowedResourceGroupsForDomainInput(
                domain_name=domain_fixture,
                add=[extra_scaling_group],
            ),
        )
        assert result.items.count(extra_scaling_group) == 1


class TestAllowedDomainsForResourceGroup:
    """Tests for resource group → domain allow/disallow (reverse direction)."""

    async def test_get_empty_allowed_domains(
        self,
        admin_v2_registry: V2ClientRegistry,
        extra_scaling_group: str,
    ) -> None:
        """Initially, a resource group has no allowed domains."""
        result = await admin_v2_registry.resource_group.get_allowed_domains_for_resource_group(
            extra_scaling_group
        )
        assert isinstance(result, AllowedDomainsPayload)
        assert result.items == []

    async def test_add_and_get_allowed_domains(
        self,
        admin_v2_registry: V2ClientRegistry,
        domain_fixture: str,
        extra_scaling_group: str,
    ) -> None:
        """Allow a domain for a resource group, then verify."""
        result = await admin_v2_registry.resource_group.update_allowed_domains_for_resource_group(
            extra_scaling_group,
            UpdateAllowedDomainsForResourceGroupInput(
                resource_group_name=extra_scaling_group,
                add=[domain_fixture],
            ),
        )
        assert isinstance(result, AllowedDomainsPayload)
        assert domain_fixture in result.items


class TestAllowedResourceGroupsForProject:
    """Tests for project → resource group allow/disallow."""

    async def test_get_empty_allowed_list(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        """Initially, a project has no allowed resource groups."""
        result = await admin_v2_registry.resource_group.get_allowed_resource_groups_for_project(
            group_fixture
        )
        assert isinstance(result, AllowedResourceGroupsPayload)
        assert result.items == []

    async def test_add_and_get_allowed(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        extra_scaling_group: str,
    ) -> None:
        """Allow a resource group for a project, then verify."""
        result = await admin_v2_registry.resource_group.update_allowed_resource_groups_for_project(
            group_fixture,
            UpdateAllowedResourceGroupsForProjectInput(
                project_id=group_fixture,
                add=[extra_scaling_group],
            ),
        )
        assert isinstance(result, AllowedResourceGroupsPayload)
        assert extra_scaling_group in result.items


class TestAllowedProjectsForResourceGroup:
    """Tests for resource group → project allow/disallow."""

    async def test_get_empty_allowed_projects(
        self,
        admin_v2_registry: V2ClientRegistry,
        extra_scaling_group: str,
    ) -> None:
        """Initially, a resource group has no allowed projects."""
        result = await admin_v2_registry.resource_group.get_allowed_projects_for_resource_group(
            extra_scaling_group
        )
        assert isinstance(result, AllowedProjectsPayload)
        assert result.items == []

    async def test_add_and_get_allowed_projects(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        extra_scaling_group: str,
    ) -> None:
        """Allow a project for a resource group, then verify."""
        result = await admin_v2_registry.resource_group.update_allowed_projects_for_resource_group(
            extra_scaling_group,
            UpdateAllowedProjectsForResourceGroupInput(
                resource_group_name=extra_scaling_group,
                add=[group_fixture],
            ),
        )
        assert isinstance(result, AllowedProjectsPayload)
        assert len(result.items) == 1
        assert result.items[0] == group_fixture
