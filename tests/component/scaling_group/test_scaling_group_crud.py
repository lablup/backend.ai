from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.scaling_group import ListScalingGroupsResponse
from ai.backend.manager.models.scaling_group import (
    ScalingGroupOpts,
    scaling_groups,
    sgroups_for_domains,
    sgroups_for_groups,
)


@pytest.fixture()
async def extra_scaling_group_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
) -> AsyncIterator[str]:
    """Create a second scaling group associated with the domain AND group."""
    sgroup_name = f"extra-sgroup-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(scaling_groups).values(
                name=sgroup_name,
                description=f"Extra scaling group {sgroup_name}",
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
        await conn.execute(
            sa.insert(sgroups_for_groups).values(
                scaling_group=sgroup_name,
                group=group_fixture,
            )
        )
    yield sgroup_name
    async with db_engine.begin() as conn:
        await conn.execute(
            sgroups_for_groups.delete().where(sgroups_for_groups.c.scaling_group == sgroup_name)
        )
        await conn.execute(
            sgroups_for_domains.delete().where(sgroups_for_domains.c.scaling_group == sgroup_name)
        )
        await conn.execute(scaling_groups.delete().where(scaling_groups.c.name == sgroup_name))


@pytest.fixture()
async def private_scaling_group_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
) -> AsyncIterator[str]:
    """Create a private (is_public=False) scaling group associated with the domain."""
    sgroup_name = f"private-sgroup-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(scaling_groups).values(
                name=sgroup_name,
                description=f"Private scaling group {sgroup_name}",
                is_active=True,
                is_public=False,
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


class TestScalingGroupCRUDLifecycle:
    """Scaling group lifecycle tests: create (via fixture) → list → verify → cleanup."""

    async def test_multiple_scaling_groups_listed(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        extra_scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Multiple scaling groups created via fixtures are all visible in the list."""
        result = await admin_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(result, ListScalingGroupsResponse)
        names = [sg.name for sg in result.scaling_groups]
        assert scaling_group_fixture in names
        assert extra_scaling_group_fixture in names

    async def test_scaling_group_domain_association(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """A scaling group associated with the test domain is visible via group filter."""
        result = await admin_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(result, ListScalingGroupsResponse)
        assert any(sg.name == scaling_group_fixture for sg in result.scaling_groups)

    async def test_regular_user_sees_public_scaling_groups(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        private_scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Regular user sees public scaling groups but not private ones.

        The fixture scaling_group_fixture defaults to is_public=True, so it
        should appear. private_scaling_group_fixture is is_public=False, so
        it should NOT appear for a regular user.
        """
        result = await user_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(result, ListScalingGroupsResponse)
        names = [sg.name for sg in result.scaling_groups]
        assert scaling_group_fixture in names
        assert private_scaling_group_fixture not in names

    async def test_admin_sees_private_scaling_groups(
        self,
        admin_registry: BackendAIClientRegistry,
        private_scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Admin can see private scaling groups."""
        result = await admin_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(result, ListScalingGroupsResponse)
        names = [sg.name for sg in result.scaling_groups]
        assert private_scaling_group_fixture in names

    async def test_wsproxy_version_not_configured(
        self,
        admin_registry: BackendAIClientRegistry,
        extra_scaling_group_fixture: str,
    ) -> None:
        """Wsproxy version request for a group without wsproxy_addr raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.scaling_group.get_wsproxy_version(
                scaling_group=extra_scaling_group_fixture,
            )

    async def test_list_empty_when_no_group_association(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Listing with a non-existent group UUID returns empty or valid response."""
        fake_group_id = str(uuid.uuid4())
        result = await admin_registry.scaling_group.list_scaling_groups(
            group=fake_group_id,
        )
        assert isinstance(result, ListScalingGroupsResponse)
        assert isinstance(result.scaling_groups, list)
