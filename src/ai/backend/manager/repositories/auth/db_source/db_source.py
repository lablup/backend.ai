"""Database source for auth repository operations."""

from __future__ import annotations

import uuid as uuid_mod
from datetime import UTC, datetime, timedelta
from typing import Any, NamedTuple, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload

from ai.backend.common.exception import BackendAIError, UserNotFound
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.auth.login_session_types import LoginHistoryData, LoginSessionData
from ai.backend.manager.data.auth.types import GroupMembershipData, UserData
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.errors.auth import (
    ActiveLoginSessionExistsError,
    AuthorizationFailed,
    GroupMembershipNotFoundError,
    UserCreationError,
)
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.models.group import association_groups_users, groups
from ai.backend.manager.models.hasher.types import HashInfo, PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.login_session.enums import LoginAttemptResult, LoginSessionStatus
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.models.user import (
    UserRole,
    UserRow,
    UserStatus,
    check_credential,
    compare_to_hashed_password,
    users,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.types import SearchScope

auth_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.DB_SOURCE, layer=LayerType.AUTH_DB_SOURCE)),
        RetryPolicy(
            RetryArgs(
                max_retries=5,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class LoginSessionCreationResult(NamedTuple):
    session_token: str
    expires_at: datetime


class CredentialVerificationResult(NamedTuple):
    user: sa.RowMapping
    session_token: str
    expires_at: datetime


class AuthDBSource:
    """
    Database source for auth operations.
    Handles all database operations for authentication.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @auth_db_source_resilience.apply()
    async def fetch_group_membership(self, group_id: UUID, user_id: UUID) -> GroupMembershipData:
        """Fetch group membership from database."""
        async with self._db.begin() as conn:
            query = (
                sa.select(association_groups_users.c.group_id, association_groups_users.c.user_id)
                .select_from(association_groups_users)
                .where(
                    (association_groups_users.c.group_id == group_id)
                    & (association_groups_users.c.user_id == user_id)
                )
            )
            result = await conn.execute(query)
            row = result.first()
            if not row:
                raise GroupMembershipNotFoundError(
                    extra_msg="No such project or you are not the member of it."
                )
        return GroupMembershipData(group_id=row.group_id, user_id=row.user_id)

    @auth_db_source_resilience.apply()
    async def verify_email_exists(self, email: str) -> bool:
        """Verify if email exists in the database."""
        async with self._db.begin() as conn:
            query = sa.select(users.c.email).select_from(users).where(users.c.email == email)
            result = await conn.execute(query)
            row = result.first()
            return row is not None

    @auth_db_source_resilience.apply()
    async def insert_user_with_keypair(
        self,
        user_data: dict[str, Any],
        keypair_data: dict[str, Any],
        group_name: str,
        domain_name: str,
    ) -> UserData:
        """Insert a new user with keypair and add to default group in database."""
        async with self._db.begin() as conn:
            # Create user
            query = users.insert().values(user_data)
            result = await conn.execute(query)
            if result.rowcount == 0:
                raise UserCreationError("Failed to create user")

            # Get created user
            user_query = users.select().where(users.c.email == user_data["email"])
            result = await conn.execute(user_query)
            user_row = result.first()
            if user_row is None:
                raise UserCreationError("Failed to retrieve created user")

            # Create keypair
            keypair_data["user"] = user_row.uuid
            keypair_query = keypairs.insert().values(keypair_data)
            await conn.execute(keypair_query)

            # Add to default group
            group_query = (
                sa.select(groups.c.id)
                .select_from(groups)
                .where((groups.c.domain_name == domain_name) & (groups.c.name == group_name))
            )
            result = await conn.execute(group_query)
            grp = result.first()
            if grp is not None:
                values = [{"user_id": user_row.uuid, "group_id": grp.id}]
                assoc_query = association_groups_users.insert().values(values)
                await conn.execute(assoc_query)

            return self._user_row_to_data(user_row)

    @auth_db_source_resilience.apply()
    async def modify_user_full_name(self, email: str, domain_name: str, full_name: str) -> None:
        """Modify user's full name in database."""
        async with self._db.begin() as conn:
            query = (
                sa.select(users)
                .select_from(users)
                .where((users.c.email == email) & (users.c.domain_name == domain_name))
            )
            result = await conn.execute(query)
            user_row = result.first()
            if not user_row:
                raise UserNotFound(extra_data={"email": email, "domain": domain_name})

            data = {"full_name": full_name}
            update_query = users.update().values(data).where(users.c.email == email)
            await conn.execute(update_query)

    @auth_db_source_resilience.apply()
    async def modify_user_password(self, email: str, password_info: PasswordInfo) -> None:
        """Modify user's password in database."""
        async with self._db.begin() as conn:
            data = {
                "password": password_info,  # PasswordColumn will handle the conversion
                "need_password_change": False,
                "password_changed_at": sa.func.now(),
            }
            query = users.update().values(data).where(users.c.email == email)
            await conn.execute(query)

    @auth_db_source_resilience.apply()
    async def modify_user_password_by_uuid(
        self, user_uuid: UUID, password_info: PasswordInfo
    ) -> datetime:
        """Modify user's password by UUID in database and return the password_changed_at timestamp."""
        async with self._db.begin() as conn:
            data = {
                "password": password_info,  # PasswordColumn will handle the conversion
                "need_password_change": False,
                "password_changed_at": sa.func.now(),
            }
            query = (
                sa.update(users)
                .values(data)
                .where(users.c.uuid == user_uuid)
                .returning(users.c.password_changed_at)
            )
            result = await conn.execute(query)
            password_changed_at = result.scalar()
            if password_changed_at is None:
                raise UserNotFound(extra_data={"user_uuid": str(user_uuid)})
            return cast(datetime, password_changed_at)

    @auth_db_source_resilience.apply()
    async def mark_user_and_keypairs_inactive(self, email: str) -> None:
        """Mark user and all their keypairs as inactive in database."""
        async with self._db.begin() as conn:
            # Deactivate user
            user_query = (
                users.update().values(status=UserStatus.INACTIVE).where(users.c.email == email)
            )
            await conn.execute(user_query)

            # Deactivate keypairs
            keypair_query = (
                keypairs.update().values(is_active=False).where(keypairs.c.user_id == email)
            )
            await conn.execute(keypair_query)

    @auth_db_source_resilience.apply()
    async def fetch_ssh_public_key(self, access_key: str) -> str | None:
        """Fetch SSH public key for an access key from database."""
        async with self._db.begin() as conn:
            query = sa.select(keypairs.c.ssh_public_key).where(keypairs.c.access_key == access_key)
            return await conn.scalar(query)

    @auth_db_source_resilience.apply()
    async def modify_ssh_keypair(self, access_key: str, public_key: str, private_key: str) -> None:
        """Modify SSH keypair for an access key in database."""
        async with self._db.begin() as conn:
            data = {
                "ssh_public_key": public_key,
                "ssh_private_key": private_key,
            }
            query = keypairs.update().values(data).where(keypairs.c.access_key == access_key)
            await conn.execute(query)

    def _user_row_to_data(self, row: UserRow | sa.Row[Any]) -> UserData:
        """Convert UserRow to UserData."""
        return UserData(
            uuid=row.uuid,
            username=row.username,
            email=row.email,
            password=row.password,
            need_password_change=row.need_password_change or False,
            full_name=row.full_name,
            description=row.description,
            is_active=row.status == UserStatus.ACTIVE,
            status=row.status or UserStatus.ACTIVE,
            status_info=row.status_info,
            created_at=row.created_at,
            modified_at=row.modified_at,
            password_changed_at=row.password_changed_at,
            domain_name=row.domain_name or "",
            role=row.role or UserRole.USER,
            integration_id=row.integration_id,
            resource_policy=row.resource_policy,
            sudo_session_enabled=row.sudo_session_enabled,
        )

    @auth_db_source_resilience.apply()
    async def fetch_user_info_by_access_key(self, access_key: str) -> tuple[str, UserRole]:
        """Join keypairs→users to get (domain_name, role) for the owner of *access_key*.

        Raises ``ValueError`` if the access key is unknown.
        """
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select(users.c.domain_name, users.c.role)
                .select_from(sa.join(keypairs, users, keypairs.c.user == users.c.uuid))
                .where(keypairs.c.access_key == access_key)
            )
            result = await conn.execute(query)
            row = result.first()
            if row is None:
                raise ValueError("Unknown owner access key")
            return row.domain_name, row.role

    @auth_db_source_resilience.apply()
    async def fetch_user_info_by_email(self, email: str) -> tuple[UUID, UserRole, str]:
        """Fetch (uuid, role, domain_name) for a user identified by *email*.

        Raises ``ValueError`` if the user is not found.
        """
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select(users.c.uuid, users.c.role, users.c.domain_name)
                .select_from(users)
                .where(users.c.email == email)
            )
            result = await conn.execute(query)
            row = result.first()
            if row is None:
                raise ValueError("Cannot delegate an unknown user")
            return row.uuid, row.role, row.domain_name

    async def _check_password(
        self,
        conn: sa.ext.asyncio.AsyncConnection,
        row: sa.Row[Any],
        target_password_info: PasswordInfo,
    ) -> None:
        """Verify password against stored hash. Raises AuthorizationFailed on mismatch."""
        if row.password is None:
            raise AuthorizationFailed("User credential mismatch.")
        try:
            if not compare_to_hashed_password(target_password_info.password, row.password):
                raise AuthorizationFailed("User credential mismatch.")
        except ValueError:
            raise AuthorizationFailed("User credential mismatch.") from None

    async def _check_active_session(
        self,
        conn: sa.ext.asyncio.AsyncConnection,
        user_id: UUID,
        force: bool,
    ) -> None:
        """Check for unexpired active sessions.

        Raises ActiveLoginSessionExistsError if an active session exists and force is False.
        If force is True, invalidates existing active sessions instead.
        """
        active_cond = (
            (LoginSessionRow.__table__.c.user_id == user_id)
            & (LoginSessionRow.__table__.c.status == LoginSessionStatus.ACTIVE)
            & (LoginSessionRow.__table__.c.expires_at > sa.func.now())
        )
        result = await conn.execute(
            sa.select(sa.func.count()).select_from(LoginSessionRow.__table__).where(active_cond)
        )
        active_count = result.scalar() or 0

        if active_count > 0 and not force:
            raise ActiveLoginSessionExistsError(
                extra_msg="An active login session already exists. Use force=true to override."
            )

        if active_count > 0 and force:
            await self._invalidate_active_sessions(conn, user_id)

    async def _invalidate_active_sessions(
        self,
        conn: sa.ext.asyncio.AsyncConnection,
        user_id: UUID,
    ) -> None:
        """Invalidate all unexpired active sessions for a user."""
        await conn.execute(
            sa.update(LoginSessionRow.__table__)
            .where(
                (LoginSessionRow.__table__.c.user_id == user_id)
                & (LoginSessionRow.__table__.c.status == LoginSessionStatus.ACTIVE)
                & (LoginSessionRow.__table__.c.expires_at > sa.func.now())
            )
            .values(
                status=LoginSessionStatus.INVALIDATED,
                invalidated_at=sa.func.now(),
            )
        )

    async def _migrate_password_hash(
        self,
        conn: sa.ext.asyncio.AsyncConnection,
        row: sa.Row[Any],
        domain_name: str,
        email: str,
        target_password_info: PasswordInfo,
    ) -> None:
        """Migrate password hash if the current algorithm differs from the target."""
        current_hash_info = HashInfo.from_hash_string(row.password)
        if target_password_info.need_migration(current_hash_info):
            await conn.execute(
                sa.update(users)
                .where((users.c.email == email) & (users.c.domain_name == domain_name))
                .values(password=target_password_info)
            )

    async def _record_login_history(
        self,
        conn: sa.ext.asyncio.AsyncConnection,
        user_id: UUID,
        domain_name: str,
        result: LoginAttemptResult,
        fail_reason: str | None,
    ) -> None:
        """Insert a login history record."""
        await conn.execute(
            sa.insert(LoginHistoryRow.__table__).values(
                user_id=user_id,
                domain_name=domain_name,
                result=result,
                fail_reason=fail_reason,
            )
        )

    @auth_db_source_resilience.apply()
    async def verify_credential_with_migration(
        self,
        domain_name: str,
        email: str,
        target_password_info: PasswordInfo,
        *,
        force: bool = False,
        max_session_age: int = 604800,
    ) -> CredentialVerificationResult:
        """Verify credentials, check active sessions, create login session, and record attempt.

        All DB operations happen atomically. Returns user row, session_token, and expires_at.
        Caller is responsible for writing session data to Valkey after this returns.
        """
        async with self._db.connect() as conn:
            result = await conn.execute(
                sa.select(users)
                .select_from(users)
                .where((users.c.email == email) & (users.c.domain_name == domain_name)),
            )
            row = result.first()

            if row is None:
                raise AuthorizationFailed("User credential mismatch.")

            try:
                await self._check_password(conn, row, target_password_info)
                await self._check_active_session(conn, row.uuid, force)
                await self._migrate_password_hash(
                    conn, row, domain_name, email, target_password_info
                )
            except AuthorizationFailed:
                await self._record_login_history(
                    conn,
                    row.uuid,
                    domain_name,
                    LoginAttemptResult.FAILED_INVALID_CREDENTIALS,
                    fail_reason="Invalid credentials",
                )
                await conn.commit()
                raise
            except ActiveLoginSessionExistsError:
                await self._record_login_history(
                    conn,
                    row.uuid,
                    domain_name,
                    LoginAttemptResult.FAILED_SESSION_ALREADY_EXISTS,
                    fail_reason="Active login session already exists",
                )
                await conn.commit()
                raise

            await self._record_login_history(
                conn, row.uuid, domain_name, LoginAttemptResult.SUCCESS, fail_reason=None
            )

            # Create login session
            session_token = uuid_mod.uuid4().hex
            now = datetime.now(UTC)
            expires_at = now + timedelta(seconds=max_session_age)
            access_key = row.main_access_key or ""
            await conn.execute(
                sa.insert(LoginSessionRow.__table__).values(
                    user_id=row.uuid,
                    access_key=access_key,
                    session_token=session_token,
                    status=LoginSessionStatus.ACTIVE,
                    expires_at=expires_at,
                )
            )

            await conn.commit()
            row_mapping: sa.RowMapping = row._mapping
            return CredentialVerificationResult(
                user=row_mapping,
                session_token=session_token,
                expires_at=expires_at,
            )

    @auth_db_source_resilience.apply()
    async def create_login_session(
        self,
        user_id: UUID,
        access_key: str,
        max_session_age: int = 604800,
    ) -> LoginSessionCreationResult:
        """Create a login session for hook-based authentication paths."""
        session_token = uuid_mod.uuid4().hex
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=max_session_age)
        async with self._db.connect() as conn:
            await conn.execute(
                sa.insert(LoginSessionRow.__table__).values(
                    user_id=user_id,
                    access_key=access_key,
                    session_token=session_token,
                    status=LoginSessionStatus.ACTIVE,
                    expires_at=expires_at,
                )
            )
            await conn.commit()
        return LoginSessionCreationResult(
            session_token=session_token,
            expires_at=expires_at,
        )

    @auth_db_source_resilience.apply()
    async def verify_credential_without_migration(
        self,
        domain_name: str,
        email: str,
        password: str,
    ) -> sa.RowMapping:
        """Verify credentials without password migration (for signout, etc.)"""
        return await check_credential(
            db=self._db,
            domain=domain_name,
            email=email,
            password=password,
        )

    @auth_db_source_resilience.apply()
    async def fetch_user_row_by_uuid(self, user_uuid: UUID) -> UserRow:
        """Fetch user row by UUID from database."""
        async with self._db.begin_readonly_session_read_committed() as db_session:
            user_query = (
                sa.select(UserRow)
                .where(UserRow.uuid == user_uuid)
                .options(
                    joinedload(UserRow.main_keypair),
                    selectinload(UserRow.keypairs),
                )
            )
            user_row = await db_session.scalar(user_query)
            if user_row is None:
                raise UserNotFound(extra_data=user_uuid)
            return user_row

    @auth_db_source_resilience.apply()
    async def fetch_current_time(self) -> datetime:
        """Fetch current time from database."""
        async with self._db.begin_readonly() as db_conn:
            result = await db_conn.scalar(sa.select(sa.func.now()))
            if result is None:
                raise InternalServerError("Failed to retrieve current database timestamp")
            return result

    # --- Login Session ---

    @auth_db_source_resilience.apply()
    @auth_db_source_resilience.apply()
    async def invalidate_session_by_token(self, session_token: str) -> None:
        """Invalidate a single login session by its token."""
        async with self._db.begin_session() as db_session:
            query = (
                sa.update(LoginSessionRow)
                .where(
                    (LoginSessionRow.session_token == session_token)
                    & (LoginSessionRow.status == LoginSessionStatus.ACTIVE)
                )
                .values(
                    status=LoginSessionStatus.INVALIDATED,
                    invalidated_at=sa.func.now(),
                )
            )
            await db_session.execute(query)

    async def invalidate_sessions_by_user(self, user_id: UUID) -> None:
        """Invalidate all active login sessions for a user."""
        async with self._db.begin_session() as db_session:
            query = (
                sa.update(LoginSessionRow)
                .where(
                    (LoginSessionRow.user_id == user_id)
                    & (LoginSessionRow.status == LoginSessionStatus.ACTIVE)
                )
                .values(
                    status=LoginSessionStatus.INVALIDATED,
                    invalidated_at=sa.func.now(),
                )
            )
            await db_session.execute(query)

    @auth_db_source_resilience.apply()
    async def search_login_sessions(
        self,
        scope: SearchScope,
        querier: BatchQuerier,
    ) -> SearchResult[LoginSessionData]:
        """Search login sessions with scope and batch querier."""
        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(LoginSessionRow)
            result = await execute_batch_querier(db_session, query, querier, scope=scope)
            items = [row.LoginSessionRow.to_data() for row in result.rows]
            return SearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # --- Login History ---

    @auth_db_source_resilience.apply()
    async def search_login_history(
        self,
        scope: SearchScope,
        querier: BatchQuerier,
    ) -> SearchResult[LoginHistoryData]:
        """Search login history with scope and batch querier."""
        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(LoginHistoryRow)
            result = await execute_batch_querier(db_session, query, querier, scope=scope)
            items = [row.LoginHistoryRow.to_data() for row in result.rows]
            return SearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
