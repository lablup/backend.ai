"""Bootstrap script content kept as revisions, run against a real database."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript, BootstrapScriptID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.errors.bootstrap_script import (
    BootstrapScriptNotFound,
    DefaultBootstrapScriptPurgeForbidden,
)
from ai.backend.manager.models.bootstrap_script.purgers import NonDefaultBootstrapScriptPurger
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.bootstrap_script_revision.creators import (
    BootstrapScriptRevisionCreator,
)
from ai.backend.manager.models.bootstrap_script_revision.row import BootstrapScriptRevisionRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.testutils.db import with_tables


class TestBootstrapScriptRevision:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                UserRow,
                BootstrapScriptRow,
                BootstrapScriptRevisionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, db: ExtendedAsyncSAEngine) -> UserRepository:
        return UserRepository(
            db=db,
            v2_ops_provider=V2DBOpsProvider(db),
            share_ops_provider=ShareOpsProvider(db),
            policy_ops_provider=ResourcePolicyOpsProvider(db),
            key_provider_pool=KeyProviderPool(
                providers=[], write_provider_type=KeyProviderType.PLAIN
            ),
        )

    @pytest.fixture
    async def user_id(self, db: ExtendedAsyncSAEngine) -> UserID:
        user_id = UserID(uuid.uuid4())
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"domain-{domain_id.hex[:8]}"
        async with db.begin_session() as session:
            session.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                    integration_id=None,
                )
            )
            session.add(
                UserResourcePolicyRow(
                    name="user-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            await session.flush()
            session.add(
                UserRow(
                    uuid=user_id,
                    username=f"user-{user_id.hex[:8]}",
                    email=f"user-{user_id.hex[:8]}@example.com",
                    password=None,
                    need_password_change=False,
                    full_name="",
                    description="",
                    status=UserStatus.ACTIVE,
                    status_info="",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy="user-policy",
                    allowed_client_ip=None,
                    totp_key=None,
                    domain_id=domain_id,
                )
            )
        return user_id

    @pytest.fixture
    async def default_script(self, db: ExtendedAsyncSAEngine, user_id: UserID) -> BootstrapScriptID:
        """The user's default script, holding one revision."""
        return await self._add_script(db, user_id, BootstrapScript("echo 1"))

    @pytest.fixture
    async def deleted_default_script(
        self, db: ExtendedAsyncSAEngine, default_script: BootstrapScriptID
    ) -> BootstrapScriptID:
        async with db.begin_session() as session:
            await session.execute(
                sa.update(BootstrapScriptRow)
                .where(BootstrapScriptRow.id == default_script)
                .values(deleted_at=sa.func.now())
            )
        return default_script

    @pytest.fixture
    async def replacement_default_script(
        self, db: ExtendedAsyncSAEngine, user_id: UserID, deleted_default_script: BootstrapScriptID
    ) -> BootstrapScriptID:
        """A new default set while the old one is soft-deleted."""
        return await self._add_script(db, user_id, BootstrapScript("echo replacement"))

    async def _add_script(
        self, db: ExtendedAsyncSAEngine, user_id: UserID, script: BootstrapScript
    ) -> BootstrapScriptID:
        async with db.begin_session() as session:
            row = BootstrapScriptRow(
                entity_type=UserEntityType(), entity_id=user_id, is_default=True
            )
            session.add(row)
            await session.flush()
            session.add(
                BootstrapScriptRevisionRow(script_id=row.id, revision_number=1, script=script)
            )
            return row.id

    async def _revisions(
        self, db: ExtendedAsyncSAEngine, script_id: BootstrapScriptID
    ) -> list[tuple[int, str, UserID | None]]:
        async with db.begin_readonly_session() as session:
            rows = await session.execute(
                sa.select(
                    BootstrapScriptRevisionRow.revision_number,
                    BootstrapScriptRevisionRow.script,
                    BootstrapScriptRevisionRow.creator_id,
                )
                .where(BootstrapScriptRevisionRow.script_id == script_id)
                .order_by(BootstrapScriptRevisionRow.revision_number)
            )
            return [(row.revision_number, row.script, row.creator_id) for row in rows]

    async def test_add_appends_a_revision_and_read_returns_the_latest(
        self,
        db: ExtendedAsyncSAEngine,
        repository: UserRepository,
        user_id: UserID,
        default_script: BootstrapScriptID,
    ) -> None:
        await repository.add_default_bootstrap_script_revision(
            user_id, BootstrapScript("echo 2"), user_id
        )
        await repository.add_default_bootstrap_script_revision(
            user_id, BootstrapScript("echo 3"), user_id
        )

        current = await repository.default_bootstrap_script(user_id)

        assert current is not None
        assert (current.revision_number, current.script) == (3, "echo 3")
        assert await self._revisions(db, default_script) == [
            (1, "echo 1", None),
            (2, "echo 2", user_id),
            (3, "echo 3", user_id),
        ]

    @pytest.mark.usefixtures("replacement_default_script")
    async def test_new_default_can_replace_a_soft_deleted_one(
        self, repository: UserRepository, user_id: UserID
    ) -> None:
        current = await repository.default_bootstrap_script(user_id)

        assert current is not None
        assert current.script == "echo replacement"

    async def test_revision_is_refused_on_a_soft_deleted_script(
        self,
        db: ExtendedAsyncSAEngine,
        user_id: UserID,
        deleted_default_script: BootstrapScriptID,
    ) -> None:
        with pytest.raises(BootstrapScriptNotFound):
            async with V2DBOpsProvider(db).write_ops() as w:
                await w.create_dangling_field(
                    BootstrapScriptRevisionCreator(
                        script_id=deleted_default_script,
                        script=BootstrapScript("echo 2"),
                        creator_id=user_id,
                    )
                )

        assert await self._revisions(db, deleted_default_script) == [(1, "echo 1", None)]

    async def test_concurrent_switches_leave_one_default(
        self,
        db: ExtendedAsyncSAEngine,
        repository: UserRepository,
        user_id: UserID,
        default_script: BootstrapScriptID,
    ) -> None:
        async with db.begin_session() as session:
            rows = [
                BootstrapScriptRow(entity_type=UserEntityType(), entity_id=user_id)
                for _ in range(8)
            ]
            session.add_all(rows)
            await session.flush()
            targets = [row.id for row in rows]

        await asyncio.gather(*(repository.switch_default_bootstrap_script(t) for t in targets))

        async with db.begin_readonly_session() as session:
            defaults = await session.scalars(
                sa.select(BootstrapScriptRow.is_default).where(
                    BootstrapScriptRow.entity_id == user_id
                )
            )
            assert list(defaults).count(True) == 1

    async def test_purge_is_refused_on_the_default_script(
        self, db: ExtendedAsyncSAEngine, default_script: BootstrapScriptID
    ) -> None:
        with pytest.raises(DefaultBootstrapScriptPurgeForbidden):
            async with V2DBOpsProvider(db).write_ops() as w:
                await w.purge_field_entity(
                    NonDefaultBootstrapScriptPurger(script_id=default_script)
                )

        assert await self._revisions(db, default_script) == [(1, "echo 1", None)]
