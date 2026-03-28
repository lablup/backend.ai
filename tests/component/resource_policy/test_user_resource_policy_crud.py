"""Component tests for user resource policy v2 CRUD."""

from __future__ import annotations

import secrets

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    UpdateUserResourcePolicyInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    CreateUserResourcePolicyPayload,
)

from .conftest import UserResourcePolicyFactory


class TestUserResourcePolicyCreate:
    """Tests for user resource policy creation."""

    async def test_s1_create_returns_correct_fields(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_resource_policy_factory: UserResourcePolicyFactory,
    ) -> None:
        """S-1: Create user resource policy with all fields."""
        unique = secrets.token_hex(4)
        name = f"crud-urp-s1-{unique}"
        result = await user_resource_policy_factory(
            name=name,
            max_vfolder_count=20,
            max_quota_scope_size=1073741824,
            max_session_count_per_model_session=5,
            max_customized_image_count=10,
        )
        assert isinstance(result, CreateUserResourcePolicyPayload)
        policy = result.user_resource_policy
        assert policy.name == name
        assert policy.max_vfolder_count == 20
        assert policy.max_quota_scope_size == 1073741824
        assert policy.max_session_count_per_model_session == 5
        assert policy.max_customized_image_count == 10


class TestUserResourcePolicyGet:
    """Tests for user resource policy retrieval."""

    async def test_s1_get_by_name(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_resource_policy_factory: UserResourcePolicyFactory,
    ) -> None:
        """S-1: Get policy by name."""
        created = await user_resource_policy_factory()
        name = created.user_resource_policy.name

        result = await admin_v2_registry.resource_policy.admin_get_user_resource_policy(name)
        assert result.name == name
        assert result.max_vfolder_count == created.user_resource_policy.max_vfolder_count


class TestUserResourcePolicyUpdate:
    """Tests for user resource policy update."""

    async def test_s1_update_partial_fields(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_resource_policy_factory: UserResourcePolicyFactory,
    ) -> None:
        """S-1: Update max_vfolder_count, others unchanged."""
        created = await user_resource_policy_factory(max_vfolder_count=5)
        name = created.user_resource_policy.name

        result = await admin_v2_registry.resource_policy.admin_update_user_resource_policy(
            name, UpdateUserResourcePolicyInput(max_vfolder_count=50)
        )
        assert result.user_resource_policy.max_vfolder_count == 50
        assert (
            result.user_resource_policy.max_customized_image_count
            == created.user_resource_policy.max_customized_image_count
        )


class TestUserResourcePolicyDelete:
    """Tests for user resource policy deletion."""

    async def test_s1_delete_by_name(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_resource_policy_factory: UserResourcePolicyFactory,
    ) -> None:
        """S-1: Delete policy."""
        created = await user_resource_policy_factory()
        name = created.user_resource_policy.name

        result = await admin_v2_registry.resource_policy.admin_delete_user_resource_policy(name)
        assert result.name == name
