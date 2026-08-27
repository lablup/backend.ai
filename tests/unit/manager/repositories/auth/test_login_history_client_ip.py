"""Round-trip tests for the ``inet`` client_ip column of ``login_history``."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.login_history import LoginHistoryID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.auth.login_session_types import LoginAttemptResult
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.login_session.row import LoginHistoryRow
from ai.backend.manager.models.resource_group import ResourceGroupForDomainRow
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables

# ORM cluster registration: configure_mappers() resolves string relationships against
# the registry. These rows are reachable via relationships but are not otherwise
# imported by this test; _ORM_CLUSTER keeps them live.
_ORM_CLUSTER = (
    AgentRow,
    ResourceGroupForDomainRow,
)


@dataclass
class SampleUserData:
    user_id: UserID
    domain_name: str


class TestLoginHistoryClientIP:
    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                UserRow,
                LoginHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def sample_user(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[SampleUserData, None]:
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{uuid.uuid4()}"
        user_id = UserID(uuid.uuid4())
        email = f"test-{uuid.uuid4()}@example.com"

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="test",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name="test-user-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_id,
                    username=email,
                    email=email,
                    password=PasswordInfo(
                        password="test_password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=100_000,
                        salt_size=32,
                    ),
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy="test-user-policy",
                    need_password_change=False,
                    domain_id=domain_id,
                )
            )
            await db_sess.flush()
            await db_sess.commit()

        yield SampleUserData(user_id=user_id, domain_name=domain_name)

    async def _insert_history(
        self, db: ExtendedAsyncSAEngine, user: SampleUserData, client_ip: str | None
    ) -> LoginHistoryID:
        row_id = LoginHistoryID(uuid.uuid4())
        async with db.begin_session() as db_sess:
            db_sess.add(
                LoginHistoryRow(
                    id=row_id,
                    user_id=user.user_id,
                    domain_name=user.domain_name,
                    result=LoginAttemptResult.SUCCESS,
                    client_ip=client_ip,
                )
            )
        return row_id

    async def _read_client_ip(
        self, db: ExtendedAsyncSAEngine, row_id: LoginHistoryID
    ) -> str | None:
        async with db.begin_readonly_session() as db_sess:
            row = await db_sess.get(LoginHistoryRow, row_id)
            assert row is not None
            return row.to_data().client_ip

    @pytest.mark.parametrize("client_ip", ["203.0.113.7", "2001:db8:1:2::1", "203.0.113.0"])
    async def test_an_address_reads_back_as_the_stored_string(
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_user: SampleUserData, client_ip: str
    ) -> None:
        row_id = await self._insert_history(db_with_cleanup, sample_user, client_ip)

        value = await self._read_client_ip(db_with_cleanup, row_id)

        assert value == client_ip
        assert isinstance(value, str)

    async def test_a_missing_address_reads_back_as_none(
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_user: SampleUserData
    ) -> None:
        row_id = await self._insert_history(db_with_cleanup, sample_user, None)

        assert await self._read_client_ip(db_with_cleanup, row_id) is None

    @pytest.mark.parametrize("client_ip", ["203.0.113.7", "2001:db8:1:2::1"])
    async def test_the_column_keeps_the_value_postgres_stored_before(
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_user: SampleUserData, client_ip: str
    ) -> None:
        """The stored form is unchanged, so records written either way are the same."""
        row_id = await self._insert_history(db_with_cleanup, sample_user, client_ip)

        async with db_with_cleanup.begin_readonly() as conn:
            result = await conn.execute(
                sa.text("SELECT client_ip::text FROM login_history WHERE id = :id"),
                {"id": row_id},
            )
            assert result.scalar_one() == client_ip
