"""Database source for auth repository operations."""

from __future__ import annotations

import uuid as uuid_mod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast
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
    AuthorizationFailed,
    GroupMembershipNotFoundError,
    LoginSessionNotFoundError,
    UserCreationError,
)
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.models.group import association_groups_users, groups
from ai.backend.manager.models.hasher.types import HashInfo, PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow, keypairs
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
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.types import SearchScope
from ai.backend.manager.repositories.permission_controller.creators import UserRoleCreatorSpec
from ai.backend.manager.repositories.permission_controller.role_manager import (
    RoleManager,
    UserSystemRoleSpec,
)

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


@dataclass(frozen=True)
class ActiveSessionInfo:
    session_token: str
    created_at: datetime


@dataclass(frozen=True)
class LoginSessionCreationResult:
    session_token: str


@dataclass(frozen=True)
class CredentialVerificationResult:
    user: sa.RowMapping
    active_sessions: list[ActiveSessionInfo]  # ordered by created_at ASC


class AuthDBSource:
    """
    Database source for auth operations.
    Handles all database operations for authentication.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._role_manager = RoleManager()

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
        async with self._db.begin_session_read_committed() as db_session:
            conn = await db_session.connection()

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

            # Create RBAC system role and map user to role
            role_spec = UserSystemRoleSpec(user_id=user_row.uuid)
            role = await self._role_manager.create_system_role(db_session, role_spec)
            user_role_creator = Creator(
                spec=UserRoleCreatorSpec(user_id=user_row.uuid, role_id=role.id)
            )
            await execute_creator(db_session, user_role_creator)

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
            integration_name=row.integration_id,  # DB column is integration_id
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

    @auth_db_source_resilience.apply()
    async def fetch_user_uuid_by_email(self, email: str, domain_name: str) -> UUID | None:
        """Fetch user UUID by email and domain. Returns None if user not found."""
        async with self._db.begin_readonly() as conn:
            return await conn.scalar(
                sa.select(users.c.uuid)
                .select_from(users)
                .where((users.c.email == email) & (users.c.domain_name == domain_name))
            )

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
        """Insert a login history record (internal, within an existing connection)."""
        await conn.execute(
            sa.insert(LoginHistoryRow.__table__).values(
                user_id=user_id,
                domain_name=domain_name,
                result=result,
                fail_reason=fail_reason,
            )
        )

    @auth_db_source_resilience.apply()
    async def record_login_history(
        self,
        user_id: UUID,
        domain_name: str,
        result: LoginAttemptResult,
        fail_reason: str | None = None,
    ) -> None:
        """Insert a login history record (public, manages its own transaction)."""
        async with self._db.begin_session() as db_session:
            await db_session.execute(
                sa.insert(LoginHistoryRow.__table__).values(
                    user_id=user_id,
                    domain_name=domain_name,
                    result=result,
                    fail_reason=fail_reason,
                )
            )

    @auth_db_source_resilience.apply()
    async def verify_credential(
        self,
        domain_name: str,
        email: str,
        target_password_info: PasswordInfo,
    ) -> CredentialVerificationResult:
        """Verify credentials, migrate password hash, and fetch active sessions.

        Does NOT record login history — the caller (service layer) handles
        all history recording via try/except.
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

            await self._check_password(conn, row, target_password_info)
            await self._migrate_password_hash(conn, row, domain_name, email, target_password_info)

            # Fetch active sessions for the user within the same connection
            session_result = await conn.execute(
                sa.select(
                    LoginSessionRow.__table__.c.session_token,
                    LoginSessionRow.__table__.c.created_at,
                )
                .where(
                    (LoginSessionRow.__table__.c.user_id == row.uuid)
                    & (LoginSessionRow.__table__.c.status == LoginSessionStatus.ACTIVE)
                )
                .order_by(LoginSessionRow.__table__.c.created_at.asc())
            )
            active_sessions = [
                ActiveSessionInfo(session_token=r.session_token, created_at=r.created_at)
                for r in session_result
            ]

            await conn.commit()
            return CredentialVerificationResult(
                user=row._mapping,
                active_sessions=active_sessions,
            )

    @auth_db_source_resilience.apply()
    async def invalidate_sessions_by_tokens(self, session_tokens: list[str]) -> None:
        """Invalidate the given active login sessions in bulk.

        Rows whose status is not ACTIVE are left untouched. This method only
        invalidates the specified sessions; the caller decides whether to invoke it
        before or after ``create_login_session`` as appropriate for the surrounding
        workflow.
        """
        if not session_tokens:
            return
        async with self._db.begin_session() as db_session:
            query = (
                sa.update(LoginSessionRow)
                .where(
                    LoginSessionRow.session_token.in_(session_tokens)
                    & (LoginSessionRow.status == LoginSessionStatus.ACTIVE)
                )
                .values(
                    status=LoginSessionStatus.INVALIDATED,
                    invalidated_at=sa.func.now(),
                )
            )
            await db_session.execute(query)

    @auth_db_source_resilience.apply()
    async def create_login_session(
        self,
        user_id: UUID,
        access_key: str,
        domain_name: str,
    ) -> LoginSessionCreationResult:
        """Create a new active login session and record a successful login history entry.

        All enforcement (cap check and force-eviction decision) is performed by the
        service layer before this method is called. Eviction of old sessions, when
        needed, must also be performed by the service layer via
        ``invalidate_login_sessions_by_tokens`` prior to this call.
        """
        session_token = uuid_mod.uuid4().hex
        async with self._db.connect() as conn:
            await conn.execute(
                sa.insert(LoginSessionRow.__table__).values(
                    user_id=user_id,
                    access_key=access_key,
                    session_token=session_token,
                    status=LoginSessionStatus.ACTIVE,
                )
            )

            # Record successful login in the same transaction.
            await self._record_login_history(
                conn, user_id, domain_name, LoginAttemptResult.SUCCESS, fail_reason=None
            )

            await conn.commit()
        return LoginSessionCreationResult(session_token=session_token)

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
                    joinedload(UserRow.main_keypair).joinedload(KeyPairRow.resource_policy_row),
                    selectinload(UserRow.keypairs).joinedload(KeyPairRow.resource_policy_row),
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
    async def fetch_active_session_tokens(self, user_id: UUID) -> list[ActiveSessionInfo]:
        """Fetch active session tokens for a user, ordered by created_at ASC (oldest first)."""
        async with self._db.begin_readonly_session() as db_session:
            query = (
                sa.select(
                    LoginSessionRow.session_token,
                    LoginSessionRow.created_at,
                )
                .where(
                    (LoginSessionRow.user_id == user_id)
                    & (LoginSessionRow.status == LoginSessionStatus.ACTIVE)
                )
                .order_by(LoginSessionRow.created_at.asc())
            )
            result = await db_session.execute(query)
            return [
                ActiveSessionInfo(session_token=row.session_token, created_at=row.created_at)
                for row in result
            ]

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

    @auth_db_source_resilience.apply()
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
    async def admin_search_login_sessions(
        self,
        querier: BatchQuerier,
    ) -> SearchResult[LoginSessionData]:
        """Search all login sessions without scope restriction (admin only)."""
        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(LoginSessionRow)
            result = await execute_batch_querier(db_session, query, querier, scope=None)
            items = [row.LoginSessionRow.to_data() for row in result.rows]
            return SearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    @auth_db_source_resilience.apply()
    async def search_login_sessions(
        self,
        scope: SearchScope,
        querier: BatchQuerier,
    ) -> SearchResult[LoginSessionData]:
        """Search login sessions within a given scope."""
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

    @auth_db_source_resilience.apply()
    async def fetch_login_session_by_id(self, session_id: UUID) -> LoginSessionData:
        """Fetch a single login session by its ID.

        Raises LoginSessionNotFoundError if the session does not exist.
        """
        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(LoginSessionRow).where(LoginSessionRow.id == session_id)
            row = await db_session.scalar(query)
            if row is None:
                raise LoginSessionNotFoundError(extra_msg=f"Login session not found: {session_id}")
            return row.to_data()

    @auth_db_source_resilience.apply()
    async def revoke_session_by_id(self, session_id: UUID) -> str:
        """Revoke an active login session by its ID.

        Sets status to REVOKED and invalidated_at to current time.
        Returns the session_token of the revoked session.
        Raises LoginSessionNotFoundError if no matching active session is found.
        """
        async with self._db.begin_session() as db_session:
            query = (
                sa.update(LoginSessionRow)
                .where(
                    (LoginSessionRow.id == session_id)
                    & (LoginSessionRow.status == LoginSessionStatus.ACTIVE)
                )
                .values(
                    status=LoginSessionStatus.REVOKED,
                    invalidated_at=sa.func.now(),
                )
                .returning(LoginSessionRow.session_token)
            )
            result = await db_session.execute(query)
            session_token = result.scalar()
            if session_token is None:
                raise LoginSessionNotFoundError(
                    extra_msg=f"No active login session found with id: {session_id}"
                )
            return session_token

    # --- Login History ---

    @auth_db_source_resilience.apply()
    async def admin_search_login_history(
        self,
        querier: BatchQuerier,
    ) -> SearchResult[LoginHistoryData]:
        """Search all login history without scope restriction (admin only)."""
        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(LoginHistoryRow)
            result = await execute_batch_querier(db_session, query, querier, scope=None)
            items = [row.LoginHistoryRow.to_data() for row in result.rows]
            return SearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    @auth_db_source_resilience.apply()
    async def search_login_history(
        self,
        scope: SearchScope,
        querier: BatchQuerier,
    ) -> SearchResult[LoginHistoryData]:
        """Search login history within a given scope."""
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
