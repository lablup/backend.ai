"""Verifies the dangling personal project backfill migration against a real database.

Static analysis does not reach the migration's SQL, so the data migration is exercised
here: projects go in, the backfill runs, and the rows it wrote are read back.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.project.types import ProjectStatus, ProjectType
from ai.backend.manager.models.alembic.versions.a9c4e2f71b63_backfill_dangling_personal_project_deletion import (
    backfill,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_policy.row import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.project.db_source.db_source import ProjectDBSource
from ai.backend.testutils.db import with_tables

_OLD = datetime.now(UTC) - timedelta(days=400)


@dataclass(frozen=True)
class _Scope:
    domain_id: DomainID
    domain_name: str
    user_uuid: uuid.UUID


class TestDanglingPersonalProjectBackfill:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                UserResourcePolicyRow,
                UserRow,
                ProjectRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def scope(self, db: ExtendedAsyncSAEngine) -> _Scope:
        scope = _Scope(DomainID(uuid.uuid4()), "backfill-domain", uuid.uuid4())
        async with db.begin_session() as sess:
            sess.add(
                DomainRow(
                    id=scope.domain_id, name=scope.domain_name, description=None, is_active=True
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=0,
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name="default",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                UserRow(
                    uuid=scope.user_uuid,
                    username="backfill-user",
                    email="backfill@example.com",
                    need_password_change=False,
                    full_name="Backfill User",
                    description="",
                    status=UserStatus.ACTIVE,
                    status_info="",
                    domain_name=scope.domain_name,
                    role=UserRole.USER,
                    resource_policy="default",
                    domain_id=scope.domain_id,
                )
            )
        return scope

    async def _add_project(
        self,
        db: ExtendedAsyncSAEngine,
        scope: _Scope,
        *,
        name: str,
        project_type: ProjectType,
        creator_id: uuid.UUID | None,
    ) -> uuid.UUID:
        project_id = uuid.uuid4()
        async with db.begin_session() as sess:
            sess.add(
                ProjectRow(
                    id=project_id,
                    name=name,
                    description=None,
                    is_active=True,
                    domain_name=scope.domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    dotfiles=b"\x90",
                    resource_policy="default",
                    type=project_type,
                    status=ProjectStatus.ACTIVE,
                    creator_id=creator_id,
                    updated_at=_OLD,
                )
            )
        return project_id

    async def _run_backfill(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin() as conn:
            await conn.run_sync(backfill)

    async def _project(self, db: ExtendedAsyncSAEngine, project_id: uuid.UUID) -> ProjectRow:
        async with db.begin_readonly_session() as sess:
            row = await sess.scalar(sa.select(ProjectRow).where(ProjectRow.id == project_id))
        assert row is not None
        return row

    async def test_marks_the_dangling_project_deleted_and_leaves_the_owned_one(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        dangling = await self._add_project(
            db, scope, name="dangling", project_type=ProjectType.PERSONAL, creator_id=None
        )
        owned = await self._add_project(
            db,
            scope,
            name="owned",
            project_type=ProjectType.PERSONAL,
            creator_id=scope.user_uuid,
        )
        general = await self._add_project(
            db, scope, name="general", project_type=ProjectType.GENERAL, creator_id=None
        )

        await self._run_backfill(db)

        dangling_row = await self._project(db, dangling)
        assert dangling_row.status is ProjectStatus.DELETED
        assert dangling_row.is_active is False
        assert dangling_row.updated_at > _OLD
        owned_row = await self._project(db, owned)
        assert owned_row.status is ProjectStatus.ACTIVE
        assert owned_row.is_active is True
        assert owned_row.updated_at == _OLD
        general_row = await self._project(db, general)
        assert general_row.status is ProjectStatus.ACTIVE
        assert general_row.is_active is True

    async def test_the_backfilled_project_becomes_collectable(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        dangling = await self._add_project(
            db, scope, name="dangling", project_type=ProjectType.PERSONAL, creator_id=None
        )
        owned = await self._add_project(
            db,
            scope,
            name="owned",
            project_type=ProjectType.PERSONAL,
            creator_id=scope.user_uuid,
        )

        await self._run_backfill(db)
        db_source = ProjectDBSource(db, V2DBOpsProvider(db))
        collectable = await db_source.dangling_personal_project_ids(
            datetime.now(UTC) + timedelta(days=1), limit=10
        )

        assert collectable == [dangling]
        assert owned not in collectable
