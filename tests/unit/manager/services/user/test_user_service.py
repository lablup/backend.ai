"""
Unit tests for UserService actions:
CreateUser, BulkCreateUser, GetUser, ModifyUser, BulkModifyUser, DeleteUser,
PurgeUser, BulkPurgeUser, SearchUsers, SearchUsersByDomain, SearchUsersByProject,
AdminMonthStats, UserMonthStats.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import AccessKey, SecretKey
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.user.types import (
    BulkUserCreateResultData,
    BulkUserUpdateResultData,
    UserCreateResultData,
    UserData,
    UserInfoContext,
    UserSearchResult,
    UserStatus,
)
from ai.backend.manager.errors.user import UserConflict, UserNotFound, UserPurgeFailure
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.creator import BulkCreatorError, Creator
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import BulkUpdaterError, Updater
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.user.types import (
    DomainUserSearchScope,
    ProjectUserSearchScope,
)
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec
from ai.backend.manager.services.user.actions.admin_month_stats import AdminMonthStatsAction
from ai.backend.manager.services.user.actions.create_user import (
    BulkCreateUserAction,
    CreateUserAction,
    UserCreateSpec,
)
from ai.backend.manager.services.user.actions.delete_user import DeleteUserAction
from ai.backend.manager.services.user.actions.get_user import GetUserAction
from ai.backend.manager.services.user.actions.modify_user import (
    BulkModifyUserAction,
    ModifyUserAction,
    UserUpdateSpec,
)
from ai.backend.manager.services.user.actions.purge_user import (
    BulkPurgeUserAction,
    PurgeUserAction,
)
from ai.backend.manager.services.user.actions.search_users import SearchUsersAction
from ai.backend.manager.services.user.actions.search_users_by_domain import (
    SearchUsersByDomainAction,
)
from ai.backend.manager.services.user.actions.search_users_by_project import (
    SearchUsersByProjectAction,
)
from ai.backend.manager.services.user.actions.user_month_stats import UserMonthStatsAction
from ai.backend.manager.services.user.service import UserService
from ai.backend.manager.types import OptionalState


def _make_user_data(
    *,
    email: str = "user@example.com",
    username: str = "testuser",
    domain_name: str = "default",
    role: UserRole = UserRole.USER,
    status: UserStatus = UserStatus.ACTIVE,
    user_uuid: uuid.UUID | None = None,
) -> UserData:
    uid = user_uuid or uuid.uuid4()
    return UserData(
        id=uid,
        uuid=uid,
        username=username,
        email=email,
        need_password_change=False,
        full_name="Test User",
        description="",
        is_active=status == UserStatus.ACTIVE,
        status=status,
        status_info=None,
        created_at=datetime.now(tz=UTC),
        modified_at=datetime.now(tz=UTC),
        domain_name=domain_name,
        role=role,
        resource_policy="default",
        allowed_client_ip=None,
        totp_activated=False,
        totp_activated_at=None,
        sudo_session_enabled=False,
        main_access_key="TESTKEY1234567890",
        container_uid=None,
        container_main_gid=None,
        container_gids=None,
    )


def _make_password_info() -> PasswordInfo:
    return PasswordInfo(
        password="password123",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=600_000,
        salt_size=32,
    )


def _make_service(mock_repo: MagicMock) -> UserService:
    return UserService(
        storage_manager=MagicMock(),
        valkey_stat_client=MagicMock(),
        agent_registry=MagicMock(),
        user_repository=mock_repo,
    )


def _make_keypair_data(user_uuid: uuid.UUID | None = None) -> KeyPairData:
    return KeyPairData(
        user_id=user_uuid or uuid.uuid4(),
        access_key=AccessKey("TESTKEY1234567890"),
        secret_key=SecretKey("TESTSECRETKEY1234567890"),
        is_active=True,
        is_admin=False,
        created_at=datetime.now(tz=UTC),
        modified_at=datetime.now(tz=UTC),
        resource_policy_name="default",
        rate_limit=1000,
        ssh_public_key=None,
        ssh_private_key=None,
        dotfiles=b"",
        bootstrap_script="",
    )


class TestCreateUser:
    """Tests for UserService.create_user"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    async def test_valid_create_returns_result_with_keypair(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Valid email/domain/username returns UserCreateResultData + auto-generated keypair."""
        user_uuid = uuid.uuid4()
        user = _make_user_data(email="new@example.com", username="newuser", user_uuid=user_uuid)
        keypair = _make_keypair_data(user_uuid)
        mock_user_repository.create_user_validated = AsyncMock(
            return_value=UserCreateResultData(user=user, keypair=keypair)
        )

        creator = Creator(
            spec=UserCreatorSpec(
                email="new@example.com",
                username="newuser",
                password=_make_password_info(),
                need_password_change=False,
                domain_name="default",
            )
        )
        action = CreateUserAction(creator=creator)

        result = await service.create_user(action)

        assert result.data.user.email == "new@example.com"
        assert result.data.keypair.access_key == "TESTKEY1234567890"
        mock_user_repository.create_user_validated.assert_called_once_with(creator, None)

    async def test_create_with_group_ids(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """group_ids links to groups."""
        user = _make_user_data(email="new@example.com")
        keypair = _make_keypair_data(user.uuid)
        mock_user_repository.create_user_validated = AsyncMock(
            return_value=UserCreateResultData(user=user, keypair=keypair)
        )

        group_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        creator = Creator(
            spec=UserCreatorSpec(
                email="new@example.com",
                username="newuser",
                password=_make_password_info(),
                need_password_change=False,
                domain_name="default",
            )
        )
        action = CreateUserAction(creator=creator, group_ids=group_ids)

        result = await service.create_user(action)

        assert result.data.user.email == "new@example.com"
        mock_user_repository.create_user_validated.assert_called_once_with(creator, group_ids)

    async def test_duplicate_email_raises_conflict(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Same-domain email duplicate raises error from repository."""
        mock_user_repository.create_user_validated = AsyncMock(
            side_effect=UserConflict("Duplicate email")
        )

        creator = Creator(
            spec=UserCreatorSpec(
                email="dup@example.com",
                username="dupuser",
                password=_make_password_info(),
                need_password_change=False,
                domain_name="default",
            )
        )
        action = CreateUserAction(creator=creator)

        with pytest.raises(UserConflict):
            await service.create_user(action)


class TestBulkCreateUser:
    """Tests for UserService.bulk_create_users"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    def _make_create_spec(self, email: str, username: str) -> UserCreateSpec:
        return UserCreateSpec(
            creator=Creator(
                spec=UserCreatorSpec(
                    email=email,
                    username=username,
                    password=_make_password_info(),
                    need_password_change=False,
                    domain_name="default",
                )
            ),
        )

    async def test_bulk_create_all_success(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """5 valid users returns successes=5 + empty failures."""
        users = [_make_user_data(email=f"u{i}@example.com", username=f"u{i}") for i in range(5)]
        mock_user_repository.bulk_create_users_validated = AsyncMock(
            return_value=BulkUserCreateResultData(successes=users, failures=[])
        )

        items = [self._make_create_spec(f"u{i}@example.com", f"u{i}") for i in range(5)]
        action = BulkCreateUserAction(items=items)

        result = await service.bulk_create_users(action)

        assert result.data.success_count() == 5
        assert result.data.failure_count() == 0
        mock_user_repository.bulk_create_users_validated.assert_called_once_with(items)

    async def test_bulk_create_partial_failure_on_duplicate(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """3rd email duplicate returns 1-2 success + 3 failure + 4-5 continue."""
        successes = [
            _make_user_data(email=f"u{i}@example.com", username=f"u{i}") for i in [0, 1, 3, 4]
        ]
        failures: list[BulkCreatorError[UserRow]] = [
            BulkCreatorError(
                spec=UserCreatorSpec(
                    email="u2@example.com",
                    username="u2",
                    password=_make_password_info(),
                    need_password_change=False,
                    domain_name="default",
                ),
                exception=InvalidAPIParameters("Duplicate email"),
                index=2,
            ),
        ]
        mock_user_repository.bulk_create_users_validated = AsyncMock(
            return_value=BulkUserCreateResultData(successes=successes, failures=failures)
        )

        items = [self._make_create_spec(f"u{i}@example.com", f"u{i}") for i in range(5)]
        action = BulkCreateUserAction(items=items)

        result = await service.bulk_create_users(action)

        assert result.data.success_count() == 4
        assert result.data.failure_count() == 1
        assert result.data.failures[0].index == 2

    async def test_bulk_create_empty_items(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Empty items returns empty successes/failures."""
        mock_user_repository.bulk_create_users_validated = AsyncMock(
            return_value=BulkUserCreateResultData(successes=[], failures=[])
        )

        action = BulkCreateUserAction(items=[])

        result = await service.bulk_create_users(action)

        assert result.data.success_count() == 0
        assert result.data.failure_count() == 0


class TestGetUser:
    """Tests for UserService.get_user"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    async def test_get_existing_user_returns_user_data(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Existing UUID returns full UserData."""
        user_uuid = uuid.uuid4()
        user = _make_user_data(user_uuid=user_uuid, email="found@example.com")
        mock_user_repository.get_user_by_uuid = AsyncMock(return_value=user)

        action = GetUserAction(user_uuid=user_uuid)
        result = await service.get_user(action)

        assert result.user.uuid == user_uuid
        assert result.user.email == "found@example.com"
        mock_user_repository.get_user_by_uuid.assert_called_once_with(user_uuid)

    async def test_get_nonexistent_user_raises_not_found(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Non-existent UUID raises UserNotFound."""
        mock_user_repository.get_user_by_uuid = AsyncMock(
            side_effect=UserNotFound("User not found")
        )

        action = GetUserAction(user_uuid=uuid.uuid4())

        with pytest.raises(UserNotFound):
            await service.get_user(action)


class TestBulkModifyUser:
    """Tests for UserService.bulk_modify_users"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    async def test_bulk_modify_all_success(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """5 users all succeed."""
        users = [_make_user_data(email=f"u{i}@example.com", username=f"u{i}") for i in range(5)]
        mock_user_repository.bulk_update_users_validated = AsyncMock(
            return_value=BulkUserUpdateResultData(successes=users, failures=[])
        )

        items = [
            UserUpdateSpec(
                user_id=uuid.uuid4(),
                updater_spec=UserUpdaterSpec(
                    full_name=OptionalState.update(f"User {i}"),
                ),
            )
            for i in range(5)
        ]
        action = BulkModifyUserAction(items=items)

        result = await service.bulk_modify_users(action)

        assert result.data.success_count() == 5
        assert result.data.failure_count() == 0

    async def test_bulk_modify_partial_failure(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """4th UUID non-existent tracks failure + continues remaining."""
        successes = [
            _make_user_data(email=f"u{i}@example.com", username=f"u{i}") for i in [0, 1, 2, 4]
        ]
        failures: list[BulkUpdaterError[UserRow]] = [
            BulkUpdaterError(
                spec=UserUpdaterSpec(
                    full_name=OptionalState.update("User 3"),
                ),
                exception=UserNotFound("User not found"),
                index=3,
            ),
        ]
        mock_user_repository.bulk_update_users_validated = AsyncMock(
            return_value=BulkUserUpdateResultData(successes=successes, failures=failures)
        )

        items = [
            UserUpdateSpec(
                user_id=uuid.uuid4(),
                updater_spec=UserUpdaterSpec(
                    full_name=OptionalState.update(f"User {i}"),
                ),
            )
            for i in range(5)
        ]
        action = BulkModifyUserAction(items=items)

        result = await service.bulk_modify_users(action)

        assert result.data.success_count() == 4
        assert result.data.failure_count() == 1
        assert result.data.failures[0].index == 3

    async def test_bulk_modify_empty_items(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Empty items returns empty result."""
        mock_user_repository.bulk_update_users_validated = AsyncMock(
            return_value=BulkUserUpdateResultData(successes=[], failures=[])
        )

        action = BulkModifyUserAction(items=[])
        result = await service.bulk_modify_users(action)

        assert result.data.success_count() == 0
        assert result.data.failure_count() == 0


class TestSearchUsers:
    """Tests for UserService.search_users"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    async def test_search_with_pagination(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Pagination (limit=10/offset=0) + total_count + has_next_page."""
        users = [_make_user_data(email=f"u{i}@example.com", username=f"u{i}") for i in range(10)]
        mock_user_repository.search_users = AsyncMock(
            return_value=UserSearchResult(
                items=users,
                total_count=25,
                has_next_page=True,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        action = SearchUsersAction(querier=querier)

        result = await service.search_users(action)

        assert len(result.users) == 10
        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is False

    async def test_search_offset_beyond_total_returns_empty(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Offset > total returns empty list + has_previous_page=true."""
        mock_user_repository.search_users = AsyncMock(
            return_value=UserSearchResult(
                items=[],
                total_count=5,
                has_next_page=False,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=100))
        action = SearchUsersAction(querier=querier)

        result = await service.search_users(action)

        assert len(result.users) == 0
        assert result.total_count == 5
        assert result.has_previous_page is True
        assert result.has_next_page is False


class TestSearchUsersByDomain:
    """Tests for UserService.search_users_by_domain"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    async def test_returns_domain_scoped_users(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Returns domain-scoped users only."""
        domain_users = [
            _make_user_data(email=f"u{i}@corp.com", domain_name="corp") for i in range(3)
        ]
        mock_user_repository.search_users_by_domain = AsyncMock(
            return_value=UserSearchResult(
                items=domain_users,
                total_count=3,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        scope = DomainUserSearchScope(domain_name="corp")
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        action = SearchUsersByDomainAction(scope=scope, querier=querier)

        result = await service.search_users_by_domain(action)

        assert len(result.users) == 3
        assert result.total_count == 3
        assert all(u.domain_name == "corp" for u in result.users)
        mock_user_repository.search_users_by_domain.assert_called_once_with(
            scope=scope, querier=querier
        )

    async def test_domain_scoped_pagination(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Domain-scoped pagination with has_next_page."""
        users = [_make_user_data(email=f"u{i}@corp.com", domain_name="corp") for i in range(5)]
        mock_user_repository.search_users_by_domain = AsyncMock(
            return_value=UserSearchResult(
                items=users,
                total_count=15,
                has_next_page=True,
                has_previous_page=False,
            )
        )

        scope = DomainUserSearchScope(domain_name="corp")
        querier = BatchQuerier(pagination=OffsetPagination(limit=5, offset=0))
        action = SearchUsersByDomainAction(scope=scope, querier=querier)

        result = await service.search_users_by_domain(action)

        assert len(result.users) == 5
        assert result.total_count == 15
        assert result.has_next_page is True


class TestSearchUsersByProject:
    """Tests for UserService.search_users_by_project"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    async def test_returns_project_members_only(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Returns project members only."""
        project_id = uuid.uuid4()
        members = [_make_user_data(email=f"m{i}@example.com") for i in range(3)]
        mock_user_repository.search_users_by_project = AsyncMock(
            return_value=UserSearchResult(
                items=members,
                total_count=3,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        scope = ProjectUserSearchScope(project_id=project_id)
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        action = SearchUsersByProjectAction(scope=scope, querier=querier)

        result = await service.search_users_by_project(action)

        assert len(result.users) == 3
        assert result.total_count == 3
        mock_user_repository.search_users_by_project.assert_called_once_with(
            scope=scope, querier=querier
        )

    async def test_no_members_returns_empty_list(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """No members returns empty list."""
        project_id = uuid.uuid4()
        mock_user_repository.search_users_by_project = AsyncMock(
            return_value=UserSearchResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        scope = ProjectUserSearchScope(project_id=project_id)
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        action = SearchUsersByProjectAction(scope=scope, querier=querier)

        result = await service.search_users_by_project(action)

        assert len(result.users) == 0
        assert result.total_count == 0


class TestModifyUser:
    """Tests for UserService.modify_user"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    async def test_modify_full_name_succeeds(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Email lookup + full_name change succeeds."""
        user = _make_user_data(email="user@example.com")
        mock_user_repository.update_user_validated = AsyncMock(return_value=user)

        updater = Updater(
            spec=UserUpdaterSpec(full_name=OptionalState.update("New Name")),
            pk_value=uuid.uuid4(),
        )
        action = ModifyUserAction(email="user@example.com", updater=updater)

        result = await service.modify_user(action)

        assert result.data.email == "user@example.com"
        mock_user_repository.update_user_validated.assert_called_once_with(
            email="user@example.com", updater=updater
        )

    async def test_nonexistent_email_raises_not_found(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Non-existent email raises UserNotFound."""
        mock_user_repository.update_user_validated = AsyncMock(
            side_effect=UserNotFound("User not found")
        )

        updater = Updater(
            spec=UserUpdaterSpec(full_name=OptionalState.update("Name")),
            pk_value=uuid.uuid4(),
        )
        action = ModifyUserAction(email="missing@example.com", updater=updater)

        with pytest.raises(UserNotFound):
            await service.modify_user(action)


class TestDeleteUser:
    """Tests for UserService.delete_user"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    async def test_soft_delete_succeeds(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Email soft delete calls repository."""
        mock_user_repository.soft_delete_user_validated = AsyncMock(return_value=None)

        action = DeleteUserAction(email="user@example.com")
        result = await service.delete_user(action)

        assert result is not None
        mock_user_repository.soft_delete_user_validated.assert_called_once_with(
            email="user@example.com"
        )

    async def test_nonexistent_email_raises_not_found(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Non-existent email raises UserNotFound."""
        mock_user_repository.soft_delete_user_validated = AsyncMock(
            side_effect=UserNotFound("User not found")
        )

        action = DeleteUserAction(email="missing@example.com")

        with pytest.raises(UserNotFound):
            await service.delete_user(action)


class TestPurgeUser:
    """Tests for UserService.purge_user"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    def _make_purge_action(self, email: str = "user@example.com", **kwargs) -> PurgeUserAction:
        return PurgeUserAction(
            user_info_ctx=UserInfoContext(
                uuid=uuid.uuid4(),
                email="admin@example.com",
                main_access_key=AccessKey("ADMINKEY"),
            ),
            email=email,
            **kwargs,
        )

    async def test_active_vfolder_mounted_raises_purge_failure(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Active vfolder mounted to running kernel raises UserPurgeFailure."""
        user = _make_user_data(email="user@example.com")
        mock_user_repository.get_by_email_validated = AsyncMock(return_value=user)
        mock_user_repository.check_user_vfolder_mounted_to_active_kernels = AsyncMock(
            return_value=True
        )

        action = self._make_purge_action()

        with pytest.raises(UserPurgeFailure):
            await service.purge_user(action)

    async def test_purge_shared_vfolders_migrates_to_admin(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """purge_shared_vfolders=true migrates shared vfolders to admin."""
        user = _make_user_data(email="user@example.com")
        mock_user_repository.get_by_email_validated = AsyncMock(return_value=user)
        mock_user_repository.check_user_vfolder_mounted_to_active_kernels = AsyncMock(
            return_value=False
        )
        mock_user_repository.migrate_shared_vfolders = AsyncMock()
        mock_user_repository.delete_endpoints = AsyncMock()
        mock_user_repository.retrieve_active_sessions = AsyncMock(return_value=[])
        mock_user_repository.delete_user_vfolders = AsyncMock()
        mock_user_repository.purge_user = AsyncMock()

        action = self._make_purge_action(purge_shared_vfolders=OptionalState.update(True))
        await service.purge_user(action)

        mock_user_repository.migrate_shared_vfolders.assert_called_once()

    async def test_delegate_endpoint_ownership_transfers(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """delegate_endpoint_ownership=true transfers endpoint ownership."""
        user = _make_user_data(email="user@example.com")
        mock_user_repository.get_by_email_validated = AsyncMock(return_value=user)
        mock_user_repository.check_user_vfolder_mounted_to_active_kernels = AsyncMock(
            return_value=False
        )
        mock_user_repository.delegate_endpoint_ownership = AsyncMock()
        mock_user_repository.delete_endpoints = AsyncMock()
        mock_user_repository.retrieve_active_sessions = AsyncMock(return_value=[])
        mock_user_repository.delete_user_vfolders = AsyncMock()
        mock_user_repository.purge_user = AsyncMock()

        action = self._make_purge_action(delegate_endpoint_ownership=OptionalState.update(True))
        await service.purge_user(action)

        mock_user_repository.delegate_endpoint_ownership.assert_called_once()
        mock_user_repository.delete_endpoints.assert_called_once_with(
            user_uuid=user.uuid, delete_destroyed_only=True
        )

    async def test_active_sessions_force_terminated(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Active sessions force-terminated then purge continues."""
        user = _make_user_data(email="user@example.com")
        mock_user_repository.get_by_email_validated = AsyncMock(return_value=user)
        mock_user_repository.check_user_vfolder_mounted_to_active_kernels = AsyncMock(
            return_value=False
        )
        mock_user_repository.delete_endpoints = AsyncMock()
        mock_user_repository.delete_user_vfolders = AsyncMock()
        mock_user_repository.purge_user = AsyncMock()

        mock_session = MagicMock()
        mock_session.id = uuid.uuid4()
        mock_user_repository.retrieve_active_sessions = AsyncMock(return_value=[mock_session])
        service._agent_registry.destroy_session = AsyncMock(return_value=None)

        action = self._make_purge_action()
        await service.purge_user(action)

        service._agent_registry.destroy_session.assert_called_once()
        mock_user_repository.purge_user.assert_called_once_with("user@example.com")


class TestBulkPurgeUser:
    """Tests for UserService.bulk_purge_users"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    async def test_partial_failure_continues(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """2nd user with active kernel-mounted vfolder tracks failure + continues."""
        admin_uuid = uuid.uuid4()
        user_uuids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        admin_user = _make_user_data(
            email="admin@example.com",
            user_uuid=admin_uuid,
            role=UserRole.SUPERADMIN,
        )
        mock_user_repository.get_user_by_uuid = AsyncMock(return_value=admin_user)

        async def mock_check_vfolder(user_uuid):
            return user_uuid == user_uuids[1]

        mock_user_repository.check_user_vfolder_mounted_to_active_kernels = AsyncMock(
            side_effect=mock_check_vfolder
        )
        mock_user_repository.delete_endpoints = AsyncMock()
        mock_user_repository.retrieve_active_sessions = AsyncMock(return_value=[])
        mock_user_repository.delete_user_vfolders = AsyncMock()
        mock_user_repository.purge_user_by_uuid = AsyncMock()

        action = BulkPurgeUserAction(
            user_ids=user_uuids,
            admin_user_id=admin_uuid,
        )
        result = await service.bulk_purge_users(action)

        assert len(result.data.purged_user_ids) == 2
        assert len(result.data.failures) == 1
        assert result.data.failures[0].user_id == user_uuids[1]

    async def test_empty_user_ids_returns_empty(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Empty user_ids returns empty purged_user_ids."""
        admin_uuid = uuid.uuid4()
        admin_user = _make_user_data(email="admin@example.com", user_uuid=admin_uuid)
        mock_user_repository.get_user_by_uuid = AsyncMock(return_value=admin_user)

        action = BulkPurgeUserAction(
            user_ids=[],
            admin_user_id=admin_uuid,
        )
        result = await service.bulk_purge_users(action)

        assert len(result.data.purged_user_ids) == 0
        assert len(result.data.failures) == 0


class TestAdminMonthStats:
    """Tests for UserService.admin_month_stats"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    async def test_current_month_returns_stats(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Current month usage stats returned."""
        mock_user_repository.get_admin_time_binned_monthly_stats = AsyncMock(
            return_value=[{"month": "2026-03", "count": 10}]
        )

        action = AdminMonthStatsAction()
        result = await service.admin_month_stats(action)

        assert len(result.stats) == 1
        assert result.stats[0]["count"] == 10

    async def test_no_sessions_returns_empty(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Month with no sessions returns empty list."""
        mock_user_repository.get_admin_time_binned_monthly_stats = AsyncMock(return_value=[])

        action = AdminMonthStatsAction()
        result = await service.admin_month_stats(action)

        assert result.stats == []


class TestUserMonthStats:
    """Tests for UserService.user_month_stats"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_user_repository: MagicMock) -> UserService:
        return _make_service(mock_user_repository)

    async def test_user_month_stats_returns_stats(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Current month usage stats returned for a specific user."""
        user_uuid = uuid.uuid4()
        mock_user_repository.get_user_time_binned_monthly_stats = AsyncMock(
            return_value=[{"month": "2026-03", "sessions": 5}]
        )

        action = UserMonthStatsAction(user_id=user_uuid)
        result = await service.user_month_stats(action)

        assert len(result.stats) == 1
        mock_user_repository.get_user_time_binned_monthly_stats.assert_called_once_with(
            user_uuid=user_uuid,
            valkey_stat_client=service._valkey_stat_client,
        )

    async def test_no_sessions_returns_empty(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Month with no sessions returns empty/zero values."""
        mock_user_repository.get_user_time_binned_monthly_stats = AsyncMock(return_value=[])

        action = UserMonthStatsAction(user_id=uuid.uuid4())
        result = await service.user_month_stats(action)

        assert result.stats == []
