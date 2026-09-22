"""Runs the public_member assignment against a real database and reads the rows back.

The preset and its role are written by the revision that introduced them, so what the
chain of revisions leaves behind is what the assignment is held against.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.permission.types import RoleStatus
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.alembic.versions.c3e8a1f05b27_add_preset_scope_and_public_member_role import (
    _create_role,
    _write_preset,
)
from ai.backend.manager.models.alembic.versions.d6e2b7a4c913_assign_every_user_the_public_member_role import (
    _PRESET_ID,
    assign_roles,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    RolePresetRow,
    RolePermissionPresetRow,
    RoleRow,
    PermissionRow,
    UserRoleRow,
]

_PRESET_UUID = uuid.UUID(_PRESET_ID)


@dataclass
class _Fixture:
    users: list[uuid.UUID]
    domain_role: uuid.UUID


@pytest.fixture
async def db(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(global_entity_ids, _TABLES):
        yield global_entity_ids


@pytest.fixture
async def seeded(db: ExtendedAsyncSAEngine) -> _Fixture:
    """Two users of one domain, the public_member preset and role as the revision that
    introduced them writes them, and an auto_assign role of another preset in the
    domain."""
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"test-domain-{uuid.uuid4().hex[:8]}")
    user_ids = [uuid.uuid4() for _ in range(2)]
    domain_preset = uuid.uuid4()
    domain_role = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            UserResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=1,
                max_customized_image_count=0,
            )
        )
        session.add(
            DomainRow(
                id=domain_id,
                name=domain_name,
                description="",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
        )
        session.add(
            RolePresetRow(
                id=domain_preset,
                name="domain_member",
                scope_type=DomainEntityType(),
                auto_assign=True,
                deleted=False,
            )
        )
        await session.flush()
        for index, user_id in enumerate(user_ids):
            session.add(
                UserRow(
                    uuid=user_id,
                    username=f"user-{index}",
                    email=f"user-{index}@example.com",
                    password=PasswordInfo(
                        password="test-password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    domain_id=domain_id,
                    domain_name=domain_name,
                    resource_policy="default",
                )
            )
        session.add(
            RoleRow(
                id=domain_role,
                name=f"domain_member-{str(domain_id)[:8]}",
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
                auto_assign=True,
                role_preset_id=domain_preset,
                scope_type=DomainEntityType(),
                scope_id=domain_id,
            )
        )
        await session.commit()
    async with db.begin() as conn:
        await conn.run_sync(_write_preset)
        await conn.run_sync(_create_role)
    return _Fixture(users=user_ids, domain_role=domain_role)


async def _run(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(assign_roles)


async def _public_role(db: ExtendedAsyncSAEngine) -> RoleRow:
    async with db.begin_readonly_session() as session:
        row = await session.scalar(sa.select(RoleRow).where(RoleRow.role_preset_id == _PRESET_UUID))
        assert row is not None
        return row


async def _grants(db: ExtendedAsyncSAEngine) -> set[tuple[uuid.UUID, uuid.UUID]]:
    async with db.begin_readonly_session() as session:
        rows = (await session.execute(sa.select(UserRoleRow.user_id, UserRoleRow.role_id))).all()
    return {(user_id, role_id) for user_id, role_id in rows}


async def _stop_assigning(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin_session() as session:
        await session.execute(
            sa.update(RoleRow)
            .where(RoleRow.role_preset_id == _PRESET_UUID)
            .values(auto_assign=False)
        )


class TestAssignPublicMemberRoles:
    async def test_every_user_holds_the_public_role_alone(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _run(db)

        role = await _public_role(db)
        assert await _grants(db) == {(user_id, role.id) for user_id in seeded.users}

    async def test_a_role_that_is_not_assigned_on_its_own_is_left_out(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _stop_assigning(db)

        await _run(db)

        assert await _grants(db) == set()

    async def test_running_again_changes_nothing(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _run(db)
        before = await _grants(db)

        await _run(db)

        assert await _grants(db) == before
