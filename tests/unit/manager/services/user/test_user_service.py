"""
Unit tests for additional UserService actions:
BulkCreateUser, GetUser, BulkModifyUser, SearchUsers, SearchUsersByDomain, SearchUsersByProject.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import (
    BulkUserCreateResultData,
    BulkUserUpdateResultData,
    UserData,
    UserSearchResult,
    UserStatus,
)
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.creator import BulkCreatorError, Creator
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import BulkUpdaterError
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.user.types import (
    DomainUserSearchScope,
    ProjectUserSearchScope,
)
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec
from ai.backend.manager.services.user.actions.create_user import (
    BulkCreateUserAction,
    UserCreateSpec,
)
from ai.backend.manager.services.user.actions.get_user import GetUserAction
from ai.backend.manager.services.user.actions.modify_user import (
    BulkModifyUserAction,
    UserUpdateSpec,
)
from ai.backend.manager.services.user.actions.search_users import SearchUsersAction
from ai.backend.manager.services.user.actions.search_users_by_domain import (
    SearchUsersByDomainAction,
)
from ai.backend.manager.services.user.actions.search_users_by_project import (
    SearchUsersByProjectAction,
)
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
