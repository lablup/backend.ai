from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.scaling_group import ListScalingGroupsResponse


class TestScalingGroupList:
    @pytest.mark.asyncio
    async def test_admin_lists_scaling_groups(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Admin can list scaling groups; the fixture sgroup is visible via domain association."""
        result = await admin_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(result, ListScalingGroupsResponse)
        names = [sg.name for sg in result.scaling_groups]
        assert scaling_group_fixture in names

    @pytest.mark.asyncio
    async def test_list_scaling_groups_with_group_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Filtering by group UUID returns the domain-associated scaling group."""
        result = await admin_registry.scaling_group.list_scaling_groups(
            group=str(group_fixture),
        )
        assert isinstance(result, ListScalingGroupsResponse)
        assert any(sg.name == scaling_group_fixture for sg in result.scaling_groups)

    @pytest.mark.asyncio
    async def test_regular_user_cannot_list_scaling_groups(
        self,
        user_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        """Regular users are not permitted to list scaling groups."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.scaling_group.list_scaling_groups(
                group=str(group_fixture),
            )


class TestScalingGroupWsproxyVersion:
    @pytest.mark.asyncio
    async def test_admin_gets_wsproxy_version(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Admin requests wsproxy version for a scaling group without wsproxy_addr configured.

        The test fixture does not configure wsproxy_addr, so the server raises
        ObjectNotFound("AppProxy address") which maps to NotFoundError on the client.
        This scenario documents the expected behavior when wsproxy is not yet configured.
        """
        with pytest.raises(NotFoundError):
            await admin_registry.scaling_group.get_wsproxy_version(
                scaling_group=scaling_group_fixture,
            )

    @pytest.mark.asyncio
    async def test_get_wsproxy_version_nonexistent(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Requesting wsproxy version for a non-existent scaling group raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.scaling_group.get_wsproxy_version(
                scaling_group="nonexistent-scaling-group-xyz",
            )

    @pytest.mark.asyncio
    async def test_regular_user_cannot_get_wsproxy_version(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Regular users are not permitted to query the wsproxy version."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.scaling_group.get_wsproxy_version(
                scaling_group=scaling_group_fixture,
            )
