"""Tests for login session force option in credential verification."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.errors.auth import ActiveLoginSessionExistsError, AuthorizationFailed
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.login_session.enums import (
    LoginAttemptResult,
    LoginSessionStatus,
)
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
class SampleUserData:
    user_id: uuid.UUID
    email: str
    password: str
    domain_name: str
    access_key: str


class TestLoginSessionForce:
    """Tests for force option in verify_credential_with_migration."""

    @pytest.fixture
    async def db_with_cleanup(
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
                LoginSessionRow,
                LoginHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def auth_db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> AuthDBSource:
        return AuthDBSource(db_with_cleanup)

    @pytest.fixture
    async def sample_user(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[SampleUserData, None]:
        """Create a user with domain, resource policies, and keypair."""
        domain_name = f"test-domain-{uuid.uuid4()}"
        user_uuid = uuid.uuid4()
        email = f"test-{uuid.uuid4()}@example.com"
        password = "test_password"
        access_key = f"AKIA{uuid.uuid4().hex[:16]}"

        async with db_with_cleanup.begin_session() as db_sess:
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
            await db_sess.flush()

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

            password_info = PasswordInfo(
                password=password,
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=100_000,
                salt_size=32,
            )
            user = UserRow(
                uuid=user_uuid,
                username=email,
                email=email,
                password=password_info,
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy="test-user-policy",
                need_password_change=False,
            )
            db_sess.add(user)
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

            user.main_access_key = access_key
            await db_sess.commit()

        yield SampleUserData(
            user_id=user_uuid,
            email=email,
            password=password,
            domain_name=domain_name,
            access_key=access_key,
        )

    def _make_password_info(self, password: str = "test_password") -> PasswordInfo:
        return PasswordInfo(
            password=password,
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )

    async def _insert_active_session(
        self,
        db: ExtendedAsyncSAEngine,
        user_id: uuid.UUID,
        access_key: str,
    ) -> None:
        """Insert an active login session for the user."""
        async with db.begin() as conn:
            await conn.execute(
                sa.insert(LoginSessionRow.__table__).values(
                    user_id=user_id,
                    access_key=access_key,
                    session_token=uuid.uuid4().hex,
                    status=LoginSessionStatus.ACTIVE,
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                )
            )

    async def _count_login_history(
        self,
        db: ExtendedAsyncSAEngine,
        user_id: uuid.UUID,
        result_filter: LoginAttemptResult | None = None,
    ) -> int:
        """Count login history entries for a user."""
        async with db.begin_readonly() as conn:
            query = (
                sa.select(sa.func.count())
                .select_from(LoginHistoryRow.__table__)
                .where(LoginHistoryRow.__table__.c.user_id == user_id)
            )
            if result_filter is not None:
                query = query.where(LoginHistoryRow.__table__.c.result == result_filter)
            return await conn.scalar(query) or 0

    async def _count_active_sessions(
        self,
        db: ExtendedAsyncSAEngine,
        user_id: uuid.UUID,
    ) -> int:
        """Count active login sessions for a user."""
        async with db.begin_readonly() as conn:
            query = (
                sa.select(sa.func.count())
                .select_from(LoginSessionRow.__table__)
                .where(
                    (LoginSessionRow.__table__.c.user_id == user_id)
                    & (LoginSessionRow.__table__.c.status == LoginSessionStatus.ACTIVE)
                )
            )
            return await conn.scalar(query) or 0

    # --- Scenario 1: no active session + force=false → success ---

    async def test_login_no_active_session_without_force(
        self,
        auth_db_source: AuthDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: SampleUserData,
    ) -> None:
        result = await auth_db_source.verify_credential_with_migration(
            domain_name=sample_user.domain_name,
            email=sample_user.email,
            target_password_info=self._make_password_info(),
            force=False,
        )
        assert result.user.uuid == sample_user.user_id
        success_count = await self._count_login_history(
            db_with_cleanup,
            sample_user.user_id,
            LoginAttemptResult.SUCCESS,
        )
        assert success_count == 1

    # --- Scenario 2: no active session + force=true → success ---

    async def test_login_no_active_session_with_force(
        self,
        auth_db_source: AuthDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: SampleUserData,
    ) -> None:
        result = await auth_db_source.verify_credential_with_migration(
            domain_name=sample_user.domain_name,
            email=sample_user.email,
            target_password_info=self._make_password_info(),
            force=True,
        )
        assert result.user.uuid == sample_user.user_id
        success_count = await self._count_login_history(
            db_with_cleanup,
            sample_user.user_id,
            LoginAttemptResult.SUCCESS,
        )
        assert success_count == 1

    # --- Scenario 3: active session + force=true → invalidate + success ---

    async def test_login_active_session_with_force_invalidates_existing(
        self,
        auth_db_source: AuthDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: SampleUserData,
    ) -> None:
        user_id = sample_user.user_id
        access_key = sample_user.access_key
        await self._insert_active_session(db_with_cleanup, user_id, access_key)
        assert await self._count_active_sessions(db_with_cleanup, user_id) == 1

        result = await auth_db_source.verify_credential_with_migration(
            domain_name=sample_user.domain_name,
            email=sample_user.email,
            target_password_info=self._make_password_info(),
            force=True,
        )
        assert result.user.uuid == user_id

        # Old session invalidated, new session created → 1 active
        assert await self._count_active_sessions(db_with_cleanup, user_id) == 1
        # The new session_token should differ from the original
        assert result.session_token
        # History should show SUCCESS
        success_count = await self._count_login_history(
            db_with_cleanup,
            user_id,
            LoginAttemptResult.SUCCESS,
        )
        assert success_count == 1

    # --- Scenario 4: active session + force=false → fail ---

    async def test_login_active_session_without_force_fails(
        self,
        auth_db_source: AuthDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: SampleUserData,
    ) -> None:
        user_id = sample_user.user_id
        access_key = sample_user.access_key
        await self._insert_active_session(db_with_cleanup, user_id, access_key)
        with pytest.raises(ActiveLoginSessionExistsError):
            await auth_db_source.verify_credential_with_migration(
                domain_name=sample_user.domain_name,
                email=sample_user.email,
                target_password_info=self._make_password_info(),
                force=False,
            )

        # History should record FAILED_SESSION_ALREADY_EXISTS
        fail_count = await self._count_login_history(
            db_with_cleanup,
            user_id,
            LoginAttemptResult.FAILED_SESSION_ALREADY_EXISTS,
        )
        assert fail_count == 1

    # --- Scenario 5: expired session should not block login ---

    async def test_login_expired_session_does_not_block(
        self,
        auth_db_source: AuthDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: SampleUserData,
    ) -> None:
        """A session with status=ACTIVE but expires_at in the past should not block login."""
        async with db_with_cleanup.begin() as conn:
            await conn.execute(
                sa.insert(LoginSessionRow.__table__).values(
                    user_id=sample_user.user_id,
                    access_key=sample_user.access_key,
                    session_token=uuid.uuid4().hex,
                    status=LoginSessionStatus.ACTIVE,
                    expires_at=datetime.now(UTC) - timedelta(hours=1),
                )
            )

        # Should succeed without force — expired session is ignored
        result = await auth_db_source.verify_credential_with_migration(
            domain_name=sample_user.domain_name,
            email=sample_user.email,
            target_password_info=self._make_password_info(),
            force=False,
        )
        assert result.user.uuid == sample_user.user_id

        success_count = await self._count_login_history(
            db_with_cleanup, sample_user.user_id, LoginAttemptResult.SUCCESS
        )
        assert success_count == 1

    # --- Scenario 6: invalid credentials → still fails regardless of force ---

    async def test_login_invalid_credentials_still_fails(
        self,
        auth_db_source: AuthDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: SampleUserData,
    ) -> None:
        with pytest.raises(AuthorizationFailed):
            await auth_db_source.verify_credential_with_migration(
                domain_name=sample_user.domain_name,
                email=sample_user.email,
                target_password_info=self._make_password_info("wrong_password"),
                force=False,
            )

        fail_count = await self._count_login_history(
            db_with_cleanup,
            sample_user.user_id,
            LoginAttemptResult.FAILED_INVALID_CREDENTIALS,
        )
        assert fail_count == 1

    # --- Scenario 7: login → logout → re-login without force succeeds ---

    async def test_login_logout_relogin_succeeds(
        self,
        auth_db_source: AuthDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: SampleUserData,
    ) -> None:
        """After logout (session invalidated), re-login should succeed without force."""
        # First login
        result1 = await auth_db_source.verify_credential_with_migration(
            domain_name=sample_user.domain_name,
            email=sample_user.email,
            target_password_info=self._make_password_info(),
        )
        assert result1.session_token
        assert await self._count_active_sessions(db_with_cleanup, sample_user.user_id) == 1

        # Logout (invalidate session by token)
        await auth_db_source.invalidate_session_by_token(result1.session_token)
        assert await self._count_active_sessions(db_with_cleanup, sample_user.user_id) == 0

        # Re-login without force should succeed
        result2 = await auth_db_source.verify_credential_with_migration(
            domain_name=sample_user.domain_name,
            email=sample_user.email,
            target_password_info=self._make_password_info(),
            force=False,
        )
        assert result2.user.uuid == sample_user.user_id
        assert result2.session_token != result1.session_token
        assert await self._count_active_sessions(db_with_cleanup, sample_user.user_id) == 1
