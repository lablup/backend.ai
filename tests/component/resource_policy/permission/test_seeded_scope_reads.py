"""A caller holding nothing but the seed roles reads the policies their scopes are
subject to.

The scenario suite plants a role of its own before calling, so it passes whatever the
declaration states. These read through the roles a user comes to hold on their own, and
fail where the declaration does not grant the read.
"""

from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.entity.project import ProjectID


class TestSeedRolesOpenTheirOwnPolicies:
    async def test_caller_reads_their_keypair_policy(
        self,
        seeded_caller_registry: V2ClientRegistry,
        resource_policy_fixture: str,
    ) -> None:
        result = await seeded_caller_registry.resource_policy.get_my_keypair_resource_policy()
        assert result.name == resource_policy_fixture

    async def test_caller_reads_their_user_policy(
        self,
        seeded_caller_registry: V2ClientRegistry,
        resource_policy_fixture: str,
    ) -> None:
        result = await seeded_caller_registry.resource_policy.get_my_user_resource_policy()
        assert result.name == resource_policy_fixture

    async def test_caller_reads_the_policy_of_their_project(
        self,
        seeded_caller_registry: V2ClientRegistry,
        seeded_project: ProjectID,
        resource_policy_fixture: str,
    ) -> None:
        result = await seeded_caller_registry.resource_policy.get_project_resource_policy(
            str(seeded_project)
        )
        assert result.name == resource_policy_fixture

    async def test_caller_is_refused_a_project_they_are_not_on(
        self,
        seeded_caller_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await seeded_caller_registry.resource_policy.get_project_resource_policy(
                str(uuid.uuid4())
            )
