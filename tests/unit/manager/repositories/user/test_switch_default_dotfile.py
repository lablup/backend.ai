"""Moving the default of a dotfile path, run against a real database."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.errors.storage import DotfileNotFound
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.testutils.db import with_tables


class TestSwitchDefaultDotfile:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [VirtualEntityRow, DotfileRow]):
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
        async with db.begin_session() as session:
            session.add(VirtualEntityRow(entity_type=UserEntityType(), entity_id=user_id))
        return user_id

    @pytest.fixture
    async def other_user_id(self, db: ExtendedAsyncSAEngine) -> UserID:
        user_id = UserID(uuid.uuid4())
        async with db.begin_session() as session:
            session.add(VirtualEntityRow(entity_type=UserEntityType(), entity_id=user_id))
        return user_id

    async def _add(
        self, db: ExtendedAsyncSAEngine, owner: UserID, path: str, *, is_default: bool
    ) -> DotfileID:
        async with db.begin_session() as session:
            row = DotfileRow(
                entity_type=UserEntityType(),
                entity_id=owner,
                path=path,
                perm="644",
                data=path,
                is_default=is_default,
            )
            session.add(row)
            await session.flush()
            return row.id

    async def _defaults(self, db: ExtendedAsyncSAEngine, owner: UserID) -> dict[DotfileID, bool]:
        async with db.begin_readonly_session() as session:
            rows = await session.execute(
                sa.select(DotfileRow.id, DotfileRow.is_default).where(DotfileRow.entity_id == owner)
            )
            return {row.id: row.is_default for row in rows}

    async def test_moves_default_onto_the_variant(
        self, db: ExtendedAsyncSAEngine, repository: UserRepository, user_id: UserID
    ) -> None:
        current = await self._add(db, user_id, ".bashrc", is_default=True)
        variant = await self._add(db, user_id, ".bashrc", is_default=False)

        data = await repository.switch_default_dotfile(user_id, variant)

        assert data.id == variant
        assert data.is_default is True
        assert await self._defaults(db, user_id) == {current: False, variant: True}

    async def test_path_without_default_gets_one(
        self, db: ExtendedAsyncSAEngine, repository: UserRepository, user_id: UserID
    ) -> None:
        created = await self._add(db, user_id, ".vimrc", is_default=False)

        await repository.switch_default_dotfile(user_id, created)

        assert await self._defaults(db, user_id) == {created: True}

    async def test_other_paths_keep_their_default(
        self, db: ExtendedAsyncSAEngine, repository: UserRepository, user_id: UserID
    ) -> None:
        other_path = await self._add(db, user_id, ".profile", is_default=True)
        target = await self._add(db, user_id, ".bashrc", is_default=False)

        await repository.switch_default_dotfile(user_id, target)

        assert await self._defaults(db, user_id) == {other_path: True, target: True}

    async def test_another_users_dotfile_is_not_found(
        self,
        db: ExtendedAsyncSAEngine,
        repository: UserRepository,
        user_id: UserID,
        other_user_id: UserID,
    ) -> None:
        theirs = await self._add(db, other_user_id, ".bashrc", is_default=False)

        with pytest.raises(DotfileNotFound):
            await repository.switch_default_dotfile(user_id, theirs)
        assert await self._defaults(db, other_user_id) == {theirs: False}

    async def test_another_users_default_on_the_same_path_stays(
        self,
        db: ExtendedAsyncSAEngine,
        repository: UserRepository,
        user_id: UserID,
        other_user_id: UserID,
    ) -> None:
        theirs = await self._add(db, other_user_id, ".bashrc", is_default=True)
        mine = await self._add(db, user_id, ".bashrc", is_default=False)

        await repository.switch_default_dotfile(user_id, mine)

        assert await self._defaults(db, other_user_id) == {theirs: True}

    async def test_concurrent_switches_leave_one_default(
        self, db: ExtendedAsyncSAEngine, repository: UserRepository, user_id: UserID
    ) -> None:
        switches = []
        for _ in range(8):
            variant = await self._add(db, user_id, ".bashrc", is_default=False)
            switches.append(repository.switch_default_dotfile(user_id, variant))

        await asyncio.gather(*switches)

        defaults = await self._defaults(db, user_id)
        assert list(defaults.values()).count(True) == 1
