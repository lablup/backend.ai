"""Tests that verify ``client_ip`` is persisted on ``login_history`` rows.

The login_history flow is driven by ``AuthDBSource`` — every public mutation
method that writes a history row (``create_login_session``,
``record_login_history``, ``delete_session_by_token``, ``delete_session_by_id``,
``delete_sessions_by_user``, ``delete_sessions_by_tokens``) accepts a
``client_ip`` kwarg and we want to keep the contract that the value flows
into the column verbatim (or stays NULL for system-driven events).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.login_session.enums import LoginAttemptResult
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.auth.db_source.db_source import AuthDBSource
from ai.backend.testutils.db import with_tables


@dataclass
class SampleUser:
    user_id: uuid.UUID
    domain_name: str
    access_key: str


class TestLoginHistoryClientIP:
    """Every login_history-writing path on ``AuthDBSource`` records ``client_ip``."""

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                LoginClientTypeRow,
                LoginSessionRow,
                LoginHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def auth_db_source(self, db: ExtendedAsyncSAEngine) -> AuthDBSource:
        return AuthDBSource(db)

    @pytest.fixture
    async def sample(self, db: ExtendedAsyncSAEngine) -> AsyncGenerator[SampleUser, None]:
        domain_name = f"test-domain-{uuid.uuid4()}"
        user_uuid = uuid.uuid4()
        email = f"test-{uuid.uuid4()}@example.com"
        access_key = f"AKIA{uuid.uuid4().hex[:16]}"

        async with db.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
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
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name="test-keypair-policy",
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=2,
                    max_containers_per_session=10,
                    idle_timeout=3600,
                )
            )
            await db_sess.flush()

            user_row = UserRow(
                uuid=user_uuid,
                username=email,
                email=email,
                password=None,
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy="test-user-policy",
                need_password_change=False,
            )
            db_sess.add(user_row)
            await db_sess.flush()

            keypair = KeyPairRow(
                access_key=access_key,
                secret_key="test_secret_key",
                user_id=email,
                user=user_uuid,
                is_active=True,
                resource_policy="test-keypair-policy",
            )
            db_sess.add(keypair)
            await db_sess.flush()
            user_row.main_access_key = access_key
            await db_sess.commit()

        yield SampleUser(user_id=user_uuid, domain_name=domain_name, access_key=access_key)

    @staticmethod
    async def _fetch_client_ips(
        db: ExtendedAsyncSAEngine,
        user_id: uuid.UUID,
        result: LoginAttemptResult,
    ) -> list[str | None]:
        async with db.begin_readonly() as conn:
            rows = await conn.execute(
                sa.select(LoginHistoryRow.__table__.c.client_ip)
                .where(LoginHistoryRow.__table__.c.user_id == user_id)
                .where(LoginHistoryRow.__table__.c.result == result)
            )
            return [row.client_ip for row in rows]

    async def test_create_login_session_records_client_ip(
        self,
        auth_db_source: AuthDBSource,
        db: ExtendedAsyncSAEngine,
        sample: SampleUser,
    ) -> None:
        await auth_db_source.create_login_session(
            user_id=sample.user_id,
            access_key=sample.access_key,
            domain_name=sample.domain_name,
            client_ip="203.0.113.10",
        )
        ips = await self._fetch_client_ips(db, sample.user_id, LoginAttemptResult.SUCCESS)
        assert ips == ["203.0.113.10"]

    async def test_record_login_history_records_client_ip(
        self,
        auth_db_source: AuthDBSource,
        db: ExtendedAsyncSAEngine,
        sample: SampleUser,
    ) -> None:
        await auth_db_source.record_login_history(
            user_id=sample.user_id,
            domain_name=sample.domain_name,
            result=LoginAttemptResult.FAILED_INVALID_CREDENTIALS,
            client_ip="198.51.100.7",
        )
        ips = await self._fetch_client_ips(
            db, sample.user_id, LoginAttemptResult.FAILED_INVALID_CREDENTIALS
        )
        assert ips == ["198.51.100.7"]

    async def test_delete_session_by_token_records_client_ip(
        self,
        auth_db_source: AuthDBSource,
        db: ExtendedAsyncSAEngine,
        sample: SampleUser,
    ) -> None:
        session = await auth_db_source.create_login_session(
            user_id=sample.user_id,
            access_key=sample.access_key,
            domain_name=sample.domain_name,
            client_ip="203.0.113.10",
        )
        await auth_db_source.delete_session_by_token(
            session.session_token,
            LoginAttemptResult.LOGOUT,
            client_ip="203.0.113.99",
        )
        ips = await self._fetch_client_ips(db, sample.user_id, LoginAttemptResult.LOGOUT)
        assert ips == ["203.0.113.99"]

    async def test_delete_session_by_id_records_client_ip(
        self,
        auth_db_source: AuthDBSource,
        db: ExtendedAsyncSAEngine,
        sample: SampleUser,
    ) -> None:
        session = await auth_db_source.create_login_session(
            user_id=sample.user_id,
            access_key=sample.access_key,
            domain_name=sample.domain_name,
            client_ip="203.0.113.10",
        )
        async with db.begin_readonly() as conn:
            session_id = await conn.scalar(
                sa.select(LoginSessionRow.__table__.c.id).where(
                    LoginSessionRow.__table__.c.session_token == session.session_token
                )
            )
        assert session_id is not None
        await auth_db_source.delete_session_by_id(
            session_id,
            LoginAttemptResult.REVOKED_BY_ADMIN,
            client_ip="192.0.2.55",
        )
        ips = await self._fetch_client_ips(db, sample.user_id, LoginAttemptResult.REVOKED_BY_ADMIN)
        assert ips == ["192.0.2.55"]

    async def test_delete_sessions_by_user_records_client_ip(
        self,
        auth_db_source: AuthDBSource,
        db: ExtendedAsyncSAEngine,
        sample: SampleUser,
    ) -> None:
        for _ in range(2):
            await auth_db_source.create_login_session(
                user_id=sample.user_id,
                access_key=sample.access_key,
                domain_name=sample.domain_name,
                client_ip="203.0.113.10",
            )
        await auth_db_source.delete_sessions_by_user(
            user_id=sample.user_id,
            domain_name=sample.domain_name,
            result=LoginAttemptResult.LOGOUT,
            client_ip="198.51.100.22",
        )
        ips = await self._fetch_client_ips(db, sample.user_id, LoginAttemptResult.LOGOUT)
        assert ips == ["198.51.100.22", "198.51.100.22"]

    async def test_delete_sessions_by_tokens_leaves_client_ip_null_for_eviction(
        self,
        auth_db_source: AuthDBSource,
        db: ExtendedAsyncSAEngine,
        sample: SampleUser,
    ) -> None:
        """System-driven eviction (``EVICTED``/``EXPIRED``) is called without a
        ``client_ip`` argument by the service, so the history row remains NULL."""
        session = await auth_db_source.create_login_session(
            user_id=sample.user_id,
            access_key=sample.access_key,
            domain_name=sample.domain_name,
            client_ip="203.0.113.10",
        )
        await auth_db_source.delete_sessions_by_tokens(
            [session.session_token],
            LoginAttemptResult.EVICTED,
        )
        ips = await self._fetch_client_ips(db, sample.user_id, LoginAttemptResult.EVICTED)
        assert ips == [None]

    async def test_client_ip_defaults_to_null_when_not_provided(
        self,
        auth_db_source: AuthDBSource,
        db: ExtendedAsyncSAEngine,
        sample: SampleUser,
    ) -> None:
        await auth_db_source.create_login_session(
            user_id=sample.user_id,
            access_key=sample.access_key,
            domain_name=sample.domain_name,
        )
        ips = await self._fetch_client_ips(db, sample.user_id, LoginAttemptResult.SUCCESS)
        assert ips == [None]
