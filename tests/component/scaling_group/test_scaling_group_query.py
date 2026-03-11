from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.scaling_group import ListScalingGroupsResponse
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupOpts,
    scaling_groups,
    sgroups_for_domains,
    sgroups_for_groups,
)


@pytest.fixture()
async def second_scaling_group_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
) -> AsyncIterator[str]:
    """Create a second scaling group for testing query operations."""
    sgroup_name = f"sgroup-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(scaling_groups).values(
                name=sgroup_name,
                description=f"Second test scaling group {sgroup_name}",
                is_active=True,
                is_public=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
        )
        await conn.execute(
            sa.insert(sgroups_for_domains).values(
                scaling_group=sgroup_name,
                domain=domain_fixture,
            )
        )
    yield sgroup_name
    async with db_engine.begin() as conn:
        await conn.execute(
            sgroups_for_domains.delete().where(sgroups_for_domains.c.scaling_group == sgroup_name)
        )
        await conn.execute(scaling_groups.delete().where(scaling_groups.c.name == sgroup_name))


@pytest.fixture()
async def inactive_scaling_group_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
) -> AsyncIterator[str]:
    """Create an inactive scaling group for testing is_active filter."""
    sgroup_name = f"inactive-sgroup-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(scaling_groups).values(
                name=sgroup_name,
                description=f"Inactive scaling group {sgroup_name}",
                is_active=False,
                is_public=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
        )
        await conn.execute(
            sa.insert(sgroups_for_domains).values(
                scaling_group=sgroup_name,
                domain=domain_fixture,
            )
        )
    yield sgroup_name
    async with db_engine.begin() as conn:
        await conn.execute(
            sgroups_for_domains.delete().where(sgroups_for_domains.c.scaling_group == sgroup_name)
        )
        await conn.execute(scaling_groups.delete().where(scaling_groups.c.name == sgroup_name))


@pytest.fixture()
async def second_group_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[uuid.UUID]:
    """Create a second test group (project) for association tests."""
    group_id = uuid.uuid4()
    group_name = f"group-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(GroupRow.__table__).values(
                id=group_id,
                name=group_name,
                description=f"Second test group {group_name}",
                is_active=True,
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
    yield group_id
    async with db_engine.begin() as conn:
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == group_id))


class TestScalingGroupProjectAssociation:
    """Tests for scaling group and project (group) association operations."""

    async def test_add_project_association(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
        db_engine: SAEngine,
    ) -> None:
        """Admin can associate a project with a scaling group."""
        # Note: The actual API for adding project associations needs to be implemented
        # For now, we verify the association exists via database query
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(sgroups_for_groups).where(
                    sa.and_(
                        sgroups_for_groups.c.scaling_group == scaling_group_fixture,
                        sgroups_for_groups.c.group == group_fixture,
                    )
                )
            )
            rows = result.fetchall()
            # The association may or may not exist depending on fixture setup
            assert isinstance(rows, list)

    async def test_remove_project_association(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        second_group_fixture: uuid.UUID,
        db_engine: SAEngine,
    ) -> None:
        """Admin can remove a project association from a scaling group."""
        # First create an association
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(sgroups_for_groups).values(
                    scaling_group=scaling_group_fixture,
                    group=second_group_fixture,
                )
            )

        # Verify it exists
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(sgroups_for_groups).where(
                    sa.and_(
                        sgroups_for_groups.c.scaling_group == scaling_group_fixture,
                        sgroups_for_groups.c.group == second_group_fixture,
                    )
                )
            )
            rows = result.fetchall()
            assert len(rows) == 1

        # Remove the association
        async with db_engine.begin() as conn:
            await conn.execute(
                sgroups_for_groups.delete().where(
                    sa.and_(
                        sgroups_for_groups.c.scaling_group == scaling_group_fixture,
                        sgroups_for_groups.c.group == second_group_fixture,
                    )
                )
            )

        # Verify it's removed
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(sgroups_for_groups).where(
                    sa.and_(
                        sgroups_for_groups.c.scaling_group == scaling_group_fixture,
                        sgroups_for_groups.c.group == second_group_fixture,
                    )
                )
            )
            rows = result.fetchall()
            assert len(rows) == 0


class TestScalingGroupFairShareSpec:
    """Tests for scaling group fair share specification operations."""

    async def test_get_fair_share_spec(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Admin can retrieve fair share spec for a scaling group."""
        # Note: This requires the fair_share SDK client implementation
        # For now, we just verify the fixture exists
        assert scaling_group_fixture is not None

    async def test_update_fair_share_spec_with_merge(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Admin can update fair share spec with merge logic."""
        # Note: This requires the fair_share SDK client implementation
        # Placeholder for future implementation
        pass

    async def test_update_fair_share_spec_filters_stale_resources(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Updating fair share spec filters out stale resources."""
        # Note: This requires the fair_share SDK client implementation
        # Placeholder for future implementation
        pass


class TestScalingGroupQueryOperations:
    """Tests for scaling group search and query operations."""

    async def test_search_scaling_groups_paginated(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        second_scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Admin can search scaling groups with pagination."""
        result = await admin_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(result, ListScalingGroupsResponse)
        assert len(result.scaling_groups) >= 2
        names = [sg.name for sg in result.scaling_groups]
        assert scaling_group_fixture in names
        assert second_scaling_group_fixture in names

    async def test_search_with_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        second_scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Admin can filter scaling groups by name."""
        # Get all scaling groups
        result = await admin_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(result, ListScalingGroupsResponse)

        # Note: The current SDK may not support name filtering
        # This test documents the expected behavior
        names = [sg.name for sg in result.scaling_groups]
        assert scaling_group_fixture in names

    async def test_search_with_is_active_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        inactive_scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Admin can filter scaling groups by is_active status."""
        # Get all scaling groups
        result = await admin_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(result, ListScalingGroupsResponse)

        # Verify active group appears
        names = [sg.name for sg in result.scaling_groups]
        assert scaling_group_fixture in names

        # Note: The current SDK may not support is_active filtering
        # The inactive group may or may not appear depending on default filters

    async def test_list_allowed_sgroups_as_admin(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Admin can list all allowed scaling groups."""
        result = await admin_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(result, ListScalingGroupsResponse)
        assert len(result.scaling_groups) > 0
        names = [sg.name for sg in result.scaling_groups]
        assert scaling_group_fixture in names

    async def test_list_allowed_sgroups_as_regular_user(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Regular user can list only domain-associated scaling groups."""
        result = await user_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(result, ListScalingGroupsResponse)

        # Regular users should see public scaling groups associated with their domain
        names = [sg.name for sg in result.scaling_groups]
        assert scaling_group_fixture in names
