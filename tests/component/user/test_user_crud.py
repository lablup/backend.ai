from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.exceptions import ConflictError, InvalidRequestError, NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.user import (
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserRequest,
    DeleteUserResponse,
    GetUserResponse,
    UserStatus,
)
from ai.backend.manager.models.group import association_groups_users
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.user import users

from .conftest import UserFactory


class TestUserCreateCrud:
    """Tests for user create CRUD operations (component-level)."""

    async def test_s1_create_with_required_fields_only(
        self,
        user_factory: UserFactory,
        db_engine: SAEngine,
    ) -> None:
        """S-1: Superadmin creates user with required fields → HTTP 201, ACTIVE status, keypair auto-created."""
        result = await user_factory()

        assert isinstance(result, CreateUserResponse)
        assert result.user.status == UserStatus.ACTIVE
        assert result.user.id is not None

        # Verify keypair auto-created in DB
        async with db_engine.begin() as conn:
            row = await conn.execute(
                sa.select(keypairs.c.user, keypairs.c.is_active).where(
                    keypairs.c.user == str(result.user.id)
                )
            )
            kp = row.fetchone()
        assert kp is not None, "Keypair should be auto-created for new user"
        assert kp.is_active is True

    async def test_s3_create_with_group_ids(
        self,
        user_factory: UserFactory,
        group_fixture: uuid.UUID,
        db_engine: SAEngine,
    ) -> None:
        """S-3: User created with group_ids → verify association_groups_users mapping in DB."""
        result = await user_factory(group_ids=[str(group_fixture)])

        async with db_engine.begin() as conn:
            row = await conn.execute(
                sa.select(association_groups_users).where(
                    sa.and_(
                        association_groups_users.c.group_id == str(group_fixture),
                        association_groups_users.c.user_id == str(result.user.id),
                    )
                )
            )
            assoc = row.fetchone()
        assert assoc is not None, "User should be associated with the given group"

    async def test_s4_create_with_status_inactive(
        self,
        user_factory: UserFactory,
        db_engine: SAEngine,
    ) -> None:
        """S-4: User created with status=INACTIVE → verify user status and keypair is_active=False."""
        result = await user_factory(status=UserStatus.INACTIVE)

        assert result.user.status == UserStatus.INACTIVE

        # Verify keypair is inactive
        async with db_engine.begin() as conn:
            row = await conn.execute(
                sa.select(keypairs.c.is_active).where(keypairs.c.user == str(result.user.id))
            )
            kp = row.fetchone()
        assert kp is not None, "Keypair should exist even for INACTIVE user"
        assert kp.is_active is False, "Keypair should be inactive when user status is INACTIVE"

    async def test_s5_create_with_container_uid_gid(
        self,
        user_factory: UserFactory,
    ) -> None:
        """S-5: User created with container_uid/gid → verify container fields in response."""
        result = await user_factory(
            container_uid=1001,
            container_main_gid=2001,
            container_gids=[2001, 2002],
        )

        assert result.user.container_uid == 1001
        assert result.user.container_main_gid == 2001
        assert result.user.container_gids == [2001, 2002]

    async def test_f_biz_1_duplicate_email_raises_conflict(
        self,
        user_factory: UserFactory,
        domain_fixture: str,
        resource_policy_fixture: str,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-1: Duplicate email → ConflictError."""
        existing = await user_factory()

        with pytest.raises(ConflictError):
            await admin_registry.user.create(
                CreateUserRequest(
                    email=existing.user.email,
                    username="another-username-xyz",
                    password="test-password-1234",
                    domain_name=domain_fixture,
                    resource_policy=resource_policy_fixture,
                )
            )

    async def test_f_biz_2_nonexistent_domain_raises_error(
        self,
        resource_policy_fixture: str,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-2: Non-existent domain → error."""
        with pytest.raises((InvalidRequestError, NotFoundError)):
            await admin_registry.user.create(
                CreateUserRequest(
                    email="no-domain@test.local",
                    username="no-domain-user",
                    password="test-password-1234",
                    domain_name="nonexistent-domain-xyz",
                    resource_policy=resource_policy_fixture,
                )
            )

    async def test_f_biz_3_nonexistent_resource_policy_raises_error(
        self,
        domain_fixture: str,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-3: Non-existent resource_policy → error."""
        with pytest.raises((InvalidRequestError, NotFoundError)):
            await admin_registry.user.create(
                CreateUserRequest(
                    email="no-policy@test.local",
                    username="no-policy-user",
                    password="test-password-1234",
                    domain_name=domain_fixture,
                    resource_policy="nonexistent-policy-xyz",
                )
            )


class TestUserGetCrud:
    """Tests for user get CRUD operations (component-level)."""

    async def test_s1_admin_gets_user_by_uuid(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        """S-1: Admin gets user by UUID → all fields returned correctly."""
        result = await admin_registry.user.get(target_user.user.id)

        assert isinstance(result, GetUserResponse)
        assert result.user.id == target_user.user.id
        assert result.user.email == target_user.user.email
        assert result.user.username == target_user.user.username
        assert result.user.status == target_user.user.status
        assert result.user.resource_policy == target_user.user.resource_policy

    async def test_s2_get_inactive_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-2: Get INACTIVE user → returns user with status INACTIVE."""
        created = await user_factory(status=UserStatus.INACTIVE)

        result = await admin_registry.user.get(created.user.id)

        assert result.user.status == UserStatus.INACTIVE

    async def test_s3_get_soft_deleted_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-3: Get DELETED (soft-deleted) user → returns user with status DELETED."""
        created = await user_factory()
        await admin_registry.user.delete(DeleteUserRequest(user_id=created.user.id))

        result = await admin_registry.user.get(created.user.id)

        assert result.user.status == UserStatus.DELETED

    async def test_s5_get_user_with_container_settings(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-5: Get user with container UID/GID settings → container fields present."""
        created = await user_factory(
            container_uid=1234,
            container_main_gid=5678,
            container_gids=[5678, 5679],
        )

        result = await admin_registry.user.get(created.user.id)

        assert result.user.container_uid == 1234
        assert result.user.container_main_gid == 5678
        assert result.user.container_gids == [5678, 5679]

    async def test_f_biz_1_get_nonexistent_uuid_raises_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-1: Get non-existent UUID → NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.user.get(uuid.uuid4())


class TestUserDeleteCrud:
    """Tests for user delete CRUD operations (component-level)."""

    async def test_s1_soft_delete_active_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
        db_engine: SAEngine,
    ) -> None:
        """S-1: Admin soft deletes ACTIVE user → success=True, DB status=DELETED, keypairs deactivated."""
        created = await user_factory()

        result = await admin_registry.user.delete(DeleteUserRequest(user_id=created.user.id))

        assert isinstance(result, DeleteUserResponse)
        assert result.success is True

        # Verify DB status is DELETED
        async with db_engine.begin() as conn:
            user_row = await conn.execute(
                sa.select(users.c.status).where(users.c.uuid == str(created.user.id))
            )
            user_status = user_row.scalar()
            assert user_status == UserStatus.DELETED

            # Verify keypairs deactivated
            kp_row = await conn.execute(
                sa.select(keypairs.c.is_active).where(keypairs.c.user == str(created.user.id))
            )
            kp_active = kp_row.scalar()
            assert kp_active is False, "Keypairs should be deactivated after soft delete"

    async def test_s2_soft_delete_inactive_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
        db_engine: SAEngine,
    ) -> None:
        """S-2: Admin soft deletes INACTIVE user → success=True, DB status=DELETED."""
        created = await user_factory(status=UserStatus.INACTIVE)

        result = await admin_registry.user.delete(DeleteUserRequest(user_id=created.user.id))

        assert result.success is True

        async with db_engine.begin() as conn:
            user_row = await conn.execute(
                sa.select(users.c.status).where(users.c.uuid == str(created.user.id))
            )
            user_status = user_row.scalar()
            assert user_status == UserStatus.DELETED

    async def test_s3_soft_delete_then_get(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-3: Soft delete then re-get → user visible with status DELETED."""
        created = await user_factory()
        await admin_registry.user.delete(DeleteUserRequest(user_id=created.user.id))

        result = await admin_registry.user.get(created.user.id)

        assert result.user.status == UserStatus.DELETED

    async def test_f_biz_1_delete_nonexistent_uuid_raises_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-1: Delete non-existent UUID → NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.user.delete(DeleteUserRequest(user_id=uuid.uuid4()))

    async def test_f_biz_2_delete_already_deleted_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """F-BIZ-2: Delete already DELETED user → verify behavior (error or idempotent)."""
        created = await user_factory()
        await admin_registry.user.delete(DeleteUserRequest(user_id=created.user.id))

        # Second delete on already-deleted user: expect either error or success (idempotent)
        try:
            result = await admin_registry.user.delete(DeleteUserRequest(user_id=created.user.id))
            # Idempotent: no error raised
            assert result.success is True
        except (NotFoundError, InvalidRequestError, ConflictError):
            # Error case is also acceptable
            pass
