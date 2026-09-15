"""Tests for what naming a user as a scope reaches."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.user.queries import user_scope_reaches, user_scope_shares
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import with_tables


class TestUserScopeReaches:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                ProjectRow,
                UserResourcePolicyRow,
                UserRow,
                KeyPairResourcePolicyRow,
                VirtualEntityRow,
                EntityMembershipRow,
                ScopeBindingRow,
            ],
        ):
            yield database_connection

    async def _node(
        self, sess: AsyncSession, entity_type: EntityType, entity_id: uuid.UUID
    ) -> uuid.UUID:
        """A node as the graph writer makes one: it governs itself."""
        row = VirtualEntityRow(entity_type=entity_type, entity_id=entity_id)
        sess.add(row)
        await sess.flush()
        sess.add(ScopeBindingRow(virtual_entity_id=row.id, scope_entity_id=row.id))
        await sess.flush()
        return row.id

    async def _seed_user(
        self, sess: AsyncSession, user_id: UserID, domain: tuple[str, uuid.UUID]
    ) -> None:
        sess.add(
            UserResourcePolicyRow(
                name="default",
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        await sess.flush()
        sess.add(
            UserRow(
                uuid=user_id,
                username=f"u-{uuid.uuid4().hex[:8]}",
                email=f"{uuid.uuid4().hex[:8]}@example.com",
                password=None,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=domain[0],
                domain_id=domain[1],
                role=UserRole.USER,
                resource_policy="default",
            )
        )
        await sess.flush()

    async def _reaches(
        self, db: ExtendedAsyncSAEngine, user_id: UserID, vfolder_id: uuid.UUID
    ) -> bool:
        async with db.begin_readonly_session() as sess:
            return bool(
                await sess.scalar(
                    sa.select(user_scope_reaches(user_id, VFolderEntityType(), vfolder_id))
                )
            )

    @pytest.fixture
    async def domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> tuple[str, uuid.UUID]:
        name, domain_id = f"d-{uuid.uuid4().hex[:8]}", uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                DomainRow(
                    id=domain_id,
                    name=name,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
        return name, domain_id

    async def test_reaches_what_the_personal_project_holds(
        self, db_with_cleanup: ExtendedAsyncSAEngine, domain: tuple[str, uuid.UUID]
    ) -> None:
        """Naming the user stands for the project that is theirs alone."""
        user_id, project_id, vfolder_id = UserID(uuid.uuid4()), uuid.uuid4(), uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            await self._seed_user(sess, user_id, domain)
            sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"p-{uuid.uuid4().hex[:8]}",
                    domain_name=domain[0],
                    type=ProjectType.PERSONAL,
                    creator_id=user_id,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy="default",
                )
            )
            await sess.flush()
            await self._node(sess, UserEntityType(), user_id)
            project = await self._node(sess, ProjectEntityType(), project_id)
            vfolder = await self._node(sess, VFolderEntityType(), vfolder_id)
            sess.add(
                EntityMembershipRow(
                    virtual_entity_id=project, member_entity_id=vfolder, capped=False
                )
            )
        assert await self._reaches(db_with_cleanup, user_id, vfolder_id)

    async def test_does_not_reach_a_team_project(
        self, db_with_cleanup: ExtendedAsyncSAEngine, domain: tuple[str, uuid.UUID]
    ) -> None:
        """A project the user merely created is not theirs alone."""
        user_id, project_id, vfolder_id = UserID(uuid.uuid4()), uuid.uuid4(), uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            await self._seed_user(sess, user_id, domain)
            sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"p-{uuid.uuid4().hex[:8]}",
                    domain_name=domain[0],
                    type=ProjectType.GENERAL,
                    creator_id=user_id,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy="default",
                )
            )
            await sess.flush()
            await self._node(sess, UserEntityType(), user_id)
            project = await self._node(sess, ProjectEntityType(), project_id)
            vfolder = await self._node(sess, VFolderEntityType(), vfolder_id)
            sess.add(
                EntityMembershipRow(
                    virtual_entity_id=project, member_entity_id=vfolder, capped=False
                )
            )
        assert not await self._reaches(db_with_cleanup, user_id, vfolder_id)

    async def _shared(
        self, db: ExtendedAsyncSAEngine, user_id: UserID, vfolder_id: uuid.UUID
    ) -> bool:
        async with db.begin_readonly_session() as sess:
            return bool(
                await sess.scalar(
                    sa.select(user_scope_shares(user_id, VFolderEntityType(), vfolder_id))
                )
            )

    async def test_a_folder_shared_to_the_user_is_shared(
        self, db_with_cleanup: ExtendedAsyncSAEngine, domain: tuple[str, uuid.UUID]
    ) -> None:
        user_id, vfolder_id = UserID(uuid.uuid4()), uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            await self._seed_user(sess, user_id, domain)
            user = await self._node(sess, UserEntityType(), user_id)
            vfolder = await self._node(sess, VFolderEntityType(), vfolder_id)
            sess.add(
                EntityMembershipRow(virtual_entity_id=user, member_entity_id=vfolder, capped=True)
            )
        assert await self._shared(db_with_cleanup, user_id, vfolder_id)

    async def test_a_personal_project_folder_is_not_shared(
        self, db_with_cleanup: ExtendedAsyncSAEngine, domain: tuple[str, uuid.UUID]
    ) -> None:
        user_id, project_id, vfolder_id = UserID(uuid.uuid4()), uuid.uuid4(), uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            await self._seed_user(sess, user_id, domain)
            sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"p-{uuid.uuid4().hex[:8]}",
                    domain_name=domain[0],
                    type=ProjectType.PERSONAL,
                    creator_id=user_id,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy="default",
                )
            )
            await sess.flush()
            await self._node(sess, UserEntityType(), user_id)
            project = await self._node(sess, ProjectEntityType(), project_id)
            vfolder = await self._node(sess, VFolderEntityType(), vfolder_id)
            sess.add(
                EntityMembershipRow(
                    virtual_entity_id=project, member_entity_id=vfolder, capped=False
                )
            )
        assert await self._reaches(db_with_cleanup, user_id, vfolder_id)
        assert not await self._shared(db_with_cleanup, user_id, vfolder_id)
