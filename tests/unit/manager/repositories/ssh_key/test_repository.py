"""The SSH keypairs of a user and their default, run against a real database."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ssh_keypair.repository import SSHKeypairRepository


class TestSSHKeypairRepository:
    async def _defaults(self, db: ExtendedAsyncSAEngine, user_id: UserID) -> list[SSHKeypairID]:
        async with db.begin_readonly_session() as session:
            rows = await session.execute(
                sa.select(SSHKeypairRow.id).where(
                    SSHKeypairRow.user_id == user_id, SSHKeypairRow.is_default
                )
            )
            return [row.id for row in rows]

    async def test_upload_without_a_default_makes_it_the_default(
        self, db: ExtendedAsyncSAEngine, user_id: UserID, default_id: SSHKeypairID
    ) -> None:
        assert await self._defaults(db, user_id) == [default_id]

    async def test_upload_with_a_default_keeps_the_default(
        self,
        repository: SSHKeypairRepository,
        db: ExtendedAsyncSAEngine,
        user_id: UserID,
        default_id: SSHKeypairID,
    ) -> None:
        added = await repository.upload(user_id, "pub-2")

        assert not added.is_default
        assert await self._defaults(db, user_id) == [default_id]

    async def test_switch_default_leaves_one_default(
        self,
        repository: SSHKeypairRepository,
        db: ExtendedAsyncSAEngine,
        user_id: UserID,
        other_id: SSHKeypairID,
    ) -> None:
        switched = await repository.switch_default(other_id)

        assert switched.is_default
        assert await self._defaults(db, user_id) == [other_id]
