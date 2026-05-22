"""Tests that verify ``client_ip`` is persisted on the ``login_sessions`` row.

``create_login_session`` writes the same client_ip to both ``login_sessions`` (the
active session) and the ``login_history`` SUCCESS row (the audit log entry).
This module covers the session-row side; ``test_login_history_client_ip.py``
covers the history side.
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


class TestLoginSessionClientIP:
    """``create_login_session`` persists ``client_ip`` on the active session row."""

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
    def client_ip(self) -> str:
        return "1.2.3.4"

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
    async def _fetch_session_client_ip(
        db: ExtendedAsyncSAEngine, session_token: str
    ) -> str | None:
        async with db.begin_readonly() as conn:
            return await conn.scalar(
                sa.select(LoginSessionRow.__table__.c.client_ip).where(
                    LoginSessionRow.__table__.c.session_token == session_token
                )
            )

    async def test_create_login_session_persists_client_ip_on_session_row(
        self,
        auth_db_source: AuthDBSource,
        db: ExtendedAsyncSAEngine,
        sample: SampleUser,
        client_ip: str,
    ) -> None:
        result = await auth_db_source.create_login_session(
            user_id=sample.user_id,
            access_key=sample.access_key,
            domain_name=sample.domain_name,
            client_ip=client_ip,
        )
        stored = await self._fetch_session_client_ip(db, result.session_token)
        assert stored == client_ip

    async def test_client_ip_defaults_to_null_when_not_provided(
        self,
        auth_db_source: AuthDBSource,
        db: ExtendedAsyncSAEngine,
        sample: SampleUser,
    ) -> None:
        result = await auth_db_source.create_login_session(
            user_id=sample.user_id,
            access_key=sample.access_key,
            domain_name=sample.domain_name,
        )
        stored = await self._fetch_session_client_ip(db, result.session_token)
        assert stored is None
