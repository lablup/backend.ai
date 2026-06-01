"""
Tests for PermissionControllerRepository.ensure_user_system_roles().

Verifies that the operation creates a SYSTEM role and user-role mapping for a
user that has none, and that it is idempotent (existing roles are reused, no
duplicate role or mapping is created on repeated calls).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence

import pytest
import sqlalchemy as sa

from ai.backend.common.data.permission.types import RoleSource
from ai.backend.common.types import BinarySize, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.permission_controller.role_manager import UserSystemRoleSpec
from ai.backend.testutils.db import TableOrORM, with_tables

ENSURE_TABLES: Sequence[TableOrORM] = [
    DomainRow,
    UserResourcePolicyRow,
    KeyPairResourcePolicyRow,
    RoleRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    AssociationScopesEntitiesRow,
    PermissionRow,
]


def _password() -> PasswordInfo:
    return PasswordInfo(
        password="dummy",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=600_000,
        salt_size=32,
    )


class TestEnsureUserSystemRoles:
    """Behavior of ensure_user_system_roles (create-if-missing, idempotent)."""

    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, ENSURE_TABLES):
            yield database_connection

    @pytest.fixture
    def repository(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        return PermissionControllerRepository(db_with_tables)

    @pytest.fixture
    async def domain_name(self, db_with_tables: ExtendedAsyncSAEngine) -> str:
        name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_tables.begin_session() as session:
            session.add(
                DomainRow(
                    name=name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                )
            )
            await session.flush()
        return name

    @pytest.fixture
    async def user_resource_policy(self, db_with_tables: ExtendedAsyncSAEngine) -> str:
        policy_name = f"user-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_tables.begin_session() as session:
            session.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            await session.flush()
        return policy_name

    async def _create_user(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_name: str,
        resource_policy: str,
        with_system_role: bool = False,
    ) -> uuid.UUID:
        user_uuid = uuid.uuid4()
        async with db.begin_session() as session:
            session.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"user-{user_uuid.hex[:8]}",
                    email=f"user-{user_uuid.hex[:8]}@example.com",
                    password=_password(),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=resource_policy,
                )
            )
            await session.flush()
            if with_system_role:
                role_id = uuid.uuid4()
                session.add(
                    RoleRow(
                        id=role_id,
                        name=f"user-{user_uuid.hex[:8]}",
                        source=RoleSource.SYSTEM,
                    )
                )
                await session.flush()
                session.add(UserRoleRow(user_id=user_uuid, role_id=role_id))
                await session.flush()
        return user_uuid

    async def _count_system_roles(self, db: ExtendedAsyncSAEngine, user_id: uuid.UUID) -> int:
        async with db.begin_readonly_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(UserRoleRow)
                .join(RoleRow, UserRoleRow.role_id == RoleRow.id)
                .where(
                    sa.and_(
                        UserRoleRow.user_id == user_id,
                        RoleRow.source == RoleSource.SYSTEM,
                    )
                )
            )
            return count or 0

    async def test_creates_role_and_mapping_when_missing(
        self,
        repository: PermissionControllerRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        domain_name: str,
        user_resource_policy: str,
    ) -> None:
        """A user without a SYSTEM role gets one created together with its mapping."""
        user_id = await self._create_user(
            db_with_tables,
            domain_name=domain_name,
            resource_policy=user_resource_policy,
        )
        assert await self._count_system_roles(db_with_tables, user_id) == 0

        results = await repository.ensure_user_system_roles([UserSystemRoleSpec(user_id=user_id)])

        assert len(results) == 1
        assert results[0].user_id == user_id
        assert results[0].role_data.source == RoleSource.SYSTEM
        assert await self._count_system_roles(db_with_tables, user_id) == 1
        async with db_with_tables.begin_readonly_session() as session:
            perm_count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(PermissionRow)
                .where(PermissionRow.role_id == results[0].role_data.id)
            )
            assert (perm_count or 0) >= 1

    async def test_idempotent_reuses_existing_role(
        self,
        repository: PermissionControllerRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        domain_name: str,
        user_resource_policy: str,
    ) -> None:
        """When a SYSTEM role already exists, it is reused; repeated calls do not duplicate."""
        user_id = await self._create_user(
            db_with_tables,
            domain_name=domain_name,
            resource_policy=user_resource_policy,
            with_system_role=True,
        )
        async with db_with_tables.begin_readonly_session() as session:
            existing_role_id = await session.scalar(
                sa.select(UserRoleRow.role_id).where(UserRoleRow.user_id == user_id)
            )

        first = await repository.ensure_user_system_roles([UserSystemRoleSpec(user_id=user_id)])
        assert first[0].role_data.id == existing_role_id
        assert await self._count_system_roles(db_with_tables, user_id) == 1

        # A second call must not raise (no duplicate mapping) and stays stable.
        second = await repository.ensure_user_system_roles([UserSystemRoleSpec(user_id=user_id)])
        assert second[0].role_data.id == existing_role_id
        assert await self._count_system_roles(db_with_tables, user_id) == 1

    async def test_batch_mixed_users(
        self,
        repository: PermissionControllerRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        domain_name: str,
        user_resource_policy: str,
    ) -> None:
        """A batch with one existing and one missing role is fully ensured."""
        existing_user = await self._create_user(
            db_with_tables,
            domain_name=domain_name,
            resource_policy=user_resource_policy,
            with_system_role=True,
        )
        missing_user = await self._create_user(
            db_with_tables,
            domain_name=domain_name,
            resource_policy=user_resource_policy,
        )

        results = await repository.ensure_user_system_roles([
            UserSystemRoleSpec(user_id=existing_user),
            UserSystemRoleSpec(user_id=missing_user),
        ])

        assert {r.user_id for r in results} == {existing_user, missing_user}
        assert await self._count_system_roles(db_with_tables, existing_user) == 1
        assert await self._count_system_roles(db_with_tables, missing_user) == 1

    async def test_empty_specs_returns_empty(
        self,
        repository: PermissionControllerRepository,
    ) -> None:
        """An empty spec collection is a no-op."""
        assert await repository.ensure_user_system_roles([]) == []
