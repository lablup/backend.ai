"""Tests for the membership predicates over the virtual-entity chain."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import with_tables


class TestScopeMembershipExists:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                VirtualEntityRow,
                EntityMembershipRow,
            ],
        ):
            yield database_connection

    async def _node(
        self, sess: AsyncSession, entity_type: EntityType, entity_id: uuid.UUID
    ) -> uuid.UUID:
        row = VirtualEntityRow(entity_type=entity_type, entity_id=entity_id)
        sess.add(row)
        await sess.flush()
        return row.id

    async def _holds(
        self,
        db: ExtendedAsyncSAEngine,
        scope_type: EntityType,
        scope_id: uuid.UUID,
        member_type: EntityType,
        member_id: uuid.UUID,
    ) -> bool:
        async with db.begin_readonly_session() as sess:
            return bool(
                await sess.scalar(
                    sa.select(scope_membership_exists(scope_type, scope_id, member_type, member_id))
                )
            )

    async def test_belonging_edge_is_held(self, db_with_cleanup: ExtendedAsyncSAEngine) -> None:
        project_id, vfolder_id = uuid.uuid4(), uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            project = await self._node(sess, ProjectEntityType(), project_id)
            vfolder = await self._node(sess, VFolderEntityType(), vfolder_id)
            sess.add(
                EntityMembershipRow(
                    virtual_entity_id=project, member_entity_id=vfolder, capped=False
                )
            )
        assert await self._holds(
            db_with_cleanup, ProjectEntityType(), project_id, VFolderEntityType(), vfolder_id
        )

    async def test_capped_edge_is_held(self, db_with_cleanup: ExtendedAsyncSAEngine) -> None:
        """A share is what the scope holds under a cap, so a read still finds it."""
        project_id, vfolder_id = uuid.uuid4(), uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            project = await self._node(sess, ProjectEntityType(), project_id)
            vfolder = await self._node(sess, VFolderEntityType(), vfolder_id)
            sess.add(
                EntityMembershipRow(
                    virtual_entity_id=project, member_entity_id=vfolder, capped=True
                )
            )
        assert await self._holds(
            db_with_cleanup, ProjectEntityType(), project_id, VFolderEntityType(), vfolder_id
        )

    async def test_another_scope_does_not_hold_it(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        holder_id, other_id, vfolder_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            holder = await self._node(sess, ProjectEntityType(), holder_id)
            await self._node(sess, ProjectEntityType(), other_id)
            vfolder = await self._node(sess, VFolderEntityType(), vfolder_id)
            sess.add(
                EntityMembershipRow(
                    virtual_entity_id=holder, member_entity_id=vfolder, capped=False
                )
            )
        assert not await self._holds(
            db_with_cleanup, ProjectEntityType(), other_id, VFolderEntityType(), vfolder_id
        )

    async def test_member_type_narrows_the_answer(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        """Two entities may share an id across types; the type tells them apart."""
        project_id, shared_id = uuid.uuid4(), uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            project = await self._node(sess, ProjectEntityType(), project_id)
            vfolder = await self._node(sess, VFolderEntityType(), shared_id)
            await self._node(sess, UserEntityType(), shared_id)
            sess.add(
                EntityMembershipRow(
                    virtual_entity_id=project, member_entity_id=vfolder, capped=False
                )
            )
        assert await self._holds(
            db_with_cleanup, ProjectEntityType(), project_id, VFolderEntityType(), shared_id
        )
        assert not await self._holds(
            db_with_cleanup, ProjectEntityType(), project_id, UserEntityType(), shared_id
        )

    async def test_correlates_with_the_outer_row(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        """The member id may be a column, which is how an operation scope uses it."""
        project_id, held_id, loose_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        async with db_with_cleanup.begin_session() as sess:
            project = await self._node(sess, ProjectEntityType(), project_id)
            held = await self._node(sess, VFolderEntityType(), held_id)
            await self._node(sess, VFolderEntityType(), loose_id)
            sess.add(
                EntityMembershipRow(virtual_entity_id=project, member_entity_id=held, capped=False)
            )
        vfolders = aliased(VirtualEntityRow, name="vfolder_node")
        async with db_with_cleanup.begin_readonly_session() as sess:
            found = (
                await sess.scalars(
                    sa.select(vfolders.entity_id).where(
                        vfolders.entity_type == VFolderEntityType(),
                        scope_membership_exists(
                            ProjectEntityType(),
                            project_id,
                            VFolderEntityType(),
                            vfolders.entity_id,
                        ),
                    )
                )
            ).all()
        assert list(found) == [held_id]
