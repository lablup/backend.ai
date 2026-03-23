"""Component tests for Scaling Group visibility and permission contracts.

Tests public/private visibility and read-only permission via the client SDK (HTTP API layer).

The scaling group has no REST API v2 endpoints for CRUD (only legacy GraphQL), so
create/modify/purge/association tests live in tests/unit/manager/services/scaling_group/.
Only the SDK-accessible endpoints (list, wsproxy-version) are tested here.

Covers scenarios from:
- scaling_group/crud.md (S-VIS-* visibility scenarios)
- scaling_group/crud.md (F-AUTH-* permission scenarios)
"""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.scaling_group import ListScalingGroupsResponse
from ai.backend.manager.models.scaling_group import (
    ScalingGroupOpts,
    scaling_groups,
    sgroups_for_domains,
)


@pytest.fixture()
async def private_sgroup_for_visibility(
    db_engine: SAEngine,
    domain_fixture: str,
) -> AsyncIterator[str]:
    """Insert a private (is_public=False) scaling group with domain association; yield name."""
    name = f"private-vis-{secrets.token_hex(8)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(scaling_groups).values(
                name=name,
                description=f"Private visibility test sgroup {name}",
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
                scaling_group=name,
                domain=domain_fixture,
            )
        )
    yield name
    async with db_engine.begin() as conn:
        await conn.execute(
            sgroups_for_domains.delete().where(sgroups_for_domains.c.scaling_group == name)
        )
        await conn.execute(scaling_groups.delete().where(scaling_groups.c.name == name))


class TestScalingGroupCRUD:
    """Visibility tests for scaling groups via the SDK (HTTP API layer).

    CRUD operations (create, modify, purge) are tested in
    tests/unit/manager/services/scaling_group/test_scaling_group_crud.py
    because the scaling group has no REST API v2 endpoints for mutations.
    Only the SDK-accessible list endpoint is tested here.
    """

    async def test_s_visibility_public_sgroup_visible_to_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Public scaling group is visible to both admin and regular user."""
        admin_result = await admin_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(admin_result, ListScalingGroupsResponse)
        assert any(sg.name == scaling_group_fixture for sg in admin_result.scaling_groups)

        user_result = await user_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(user_result, ListScalingGroupsResponse)
        assert any(sg.name == scaling_group_fixture for sg in user_result.scaling_groups)

    async def test_s_visibility_private_sgroup_hidden_from_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        private_sgroup_for_visibility: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Private scaling group (is_public=False) is hidden from regular users.

        Admin can still see private sgroups via list_allowed_sgroups when is_admin=True.
        Regular users get filtered results (only public sgroups).
        """
        name = private_sgroup_for_visibility

        # Regular user should NOT see the private sgroup
        user_result = await user_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(user_result, ListScalingGroupsResponse)
        assert not any(sg.name == name for sg in user_result.scaling_groups)

        # Admin should see the private sgroup (is_admin=True bypasses is_public filter)
        admin_result = await admin_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(admin_result, ListScalingGroupsResponse)
        assert any(sg.name == name for sg in admin_result.scaling_groups)


class TestScalingGroupPermissions:
    """Permission contract tests for scaling group REST API endpoints.

    Scaling group CRUD (create / modify / purge) is ONLY accessible through
    the legacy GraphQL API, which enforces ``allowed_roles = (UserRole.SUPERADMIN,)``.
    The REST API v2 exposes only read-only endpoints (list, wsproxy-version), both
    guarded by ``auth_required`` (not ``superadmin_required``), so all authenticated
    users — including regular users — can call them.

    Because the REST layer has no create / modify / purge endpoints, 403 permission
    testing for those mutations is not applicable here.  The superadmin restriction
    is enforced at the GraphQL layer.
    """

    async def test_regular_user_can_list_scaling_groups(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """F-AUTH-LIST: Regular user can list public scaling groups (auth_required, not superadmin).

        The list_scaling_groups endpoint uses ``auth_required``, so non-admin
        users get a 200 response filtered to public scaling groups.  The fixture
        sgroup is public (is_public=True), so it should appear in the result.
        """
        result = await user_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(result, ListScalingGroupsResponse)
        names = [sg.name for sg in result.scaling_groups]
        # The fixture sgroup is public — regular user should see it
        assert scaling_group_fixture in names
