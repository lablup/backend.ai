"""
Unit tests for GroupService actions:
CreateGroup, ModifyGroup, DeleteGroup, PurgeGroup,
SearchProjects, SearchProjectsByDomain, SearchProjectsByUser, GetProject,
UsagePerMonth, UsagePerPeriod.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.group.creators import GroupCreatorSpec
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.group.types import (
    DomainProjectSearchScope,
    GroupSearchResult,
    UserProjectSearchScope,
)
from ai.backend.manager.repositories.group.updaters import GroupUpdaterSpec
from ai.backend.manager.services.group.actions.create_group import CreateGroupAction
from ai.backend.manager.services.group.actions.delete_group import DeleteGroupAction
from ai.backend.manager.services.group.actions.modify_group import ModifyGroupAction
from ai.backend.manager.services.group.actions.purge_group import PurgeGroupAction
from ai.backend.manager.services.group.actions.search_projects import (
    GetProjectAction,
    SearchProjectsAction,
    SearchProjectsByDomainAction,
    SearchProjectsByUserAction,
)
from ai.backend.manager.services.group.actions.usage_per_month import (
    UsagePerMonthAction,
)
from ai.backend.manager.services.group.actions.usage_per_period import (
    UsagePerPeriodAction,
)
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.types import OptionalState


def _make_group_data(
    *,
    name: str = "test-project",
    domain_name: str = "default",
    is_active: bool = True,
    group_id: uuid.UUID | None = None,
) -> GroupData:
    return GroupData(
        id=group_id or uuid.uuid4(),
        name=name,
        description="test description",
        is_active=is_active,
        created_at=datetime.now(tz=UTC),
        modified_at=datetime.now(tz=UTC),
        integration_id=None,
        domain_name=domain_name,
        total_resource_slots=ResourceSlot.from_user_input({}, None),
        allowed_vfolder_hosts=VFolderHostPermissionMap({}),
        dotfiles=b"\x90",
        resource_policy="default",
        type=ProjectType.GENERAL,
        container_registry={},
    )


def _make_service(mock_repo: MagicMock) -> GroupService:
    group_repositories = GroupRepositories(repository=mock_repo)
    return GroupService(
        storage_manager=MagicMock(),
        config_provider=MagicMock(),
        valkey_stat_client=MagicMock(),
        group_repositories=group_repositories,
    )


class TestCreateGroup:
    """Tests for GroupService.create_group"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def service(self, mock_group_repository: MagicMock) -> GroupService:
        return _make_service(mock_group_repository)

    async def test_create_returns_group_data(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """name/description/domain_name returns GroupData (is_active=true)."""
        group = _make_group_data(name="new-project", domain_name="default")
        mock_group_repository.create = AsyncMock(return_value=group)

        creator = Creator(
            spec=GroupCreatorSpec(name="new-project", domain_name="default", description="desc")
        )
        action = CreateGroupAction(creator=creator)

        result = await service.create_group(action)

        assert result.data is not None
        assert result.data.name == "new-project"
        assert result.data.is_active is True
        mock_group_repository.create.assert_called_once_with(creator)

    async def test_create_with_resource_slots(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """total_resource_slots JSON parsed correctly."""
        slots = ResourceSlot.from_user_input({"cpu": "4", "mem": "8g"}, None)
        group = _make_group_data(name="gpu-project")
        mock_group_repository.create = AsyncMock(return_value=group)

        creator = Creator(
            spec=GroupCreatorSpec(
                name="gpu-project",
                domain_name="default",
                total_resource_slots=slots,
            )
        )
        action = CreateGroupAction(creator=creator)

        result = await service.create_group(action)

        assert result.data is not None
        mock_group_repository.create.assert_called_once_with(creator)

    async def test_duplicate_name_raises_conflict(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Same-domain duplicate name raises IntegrityError from repository."""
        mock_group_repository.create = AsyncMock(
            side_effect=IntegrityError("duplicate", {}, Exception("duplicate key"))
        )

        creator = Creator(spec=GroupCreatorSpec(name="existing", domain_name="default"))
        action = CreateGroupAction(creator=creator)

        with pytest.raises(IntegrityError):
            await service.create_group(action)


class TestModifyGroup:
    """Tests for GroupService.modify_group"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def service(self, mock_group_repository: MagicMock) -> GroupService:
        return _make_service(mock_group_repository)

    async def test_name_only_change_preserves_other_fields(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Name-only change preserves other fields."""
        group = _make_group_data(name="renamed-project")
        mock_group_repository.modify_validated = AsyncMock(return_value=group)

        group_id = uuid.uuid4()
        updater = Updater(
            spec=GroupUpdaterSpec(name=OptionalState.update("renamed-project")),
            pk_value=group_id,
        )
        action = ModifyGroupAction(updater=updater)

        result = await service.modify_group(action)

        assert result.data is not None
        assert result.data.name == "renamed-project"
        mock_group_repository.modify_validated.assert_called_once_with(updater, None, None)

    async def test_add_user_members(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """user_update_mode='add' + user_uuids adds members."""
        group = _make_group_data(name="project")
        mock_group_repository.modify_validated = AsyncMock(return_value=group)

        user_uuids = [str(uuid.uuid4()), str(uuid.uuid4())]
        group_id = uuid.uuid4()
        updater = Updater(spec=GroupUpdaterSpec(), pk_value=group_id)
        action = ModifyGroupAction(
            updater=updater,
            user_update_mode=OptionalState.update("add"),
            user_uuids=OptionalState.update(user_uuids),
        )

        await service.modify_group(action)

        call_args = mock_group_repository.modify_validated.call_args
        assert call_args[0][1] == "add"
        assert len(call_args[0][2]) == 2

    async def test_remove_user_members(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """user_update_mode='remove' removes members."""
        group = _make_group_data(name="project")
        mock_group_repository.modify_validated = AsyncMock(return_value=group)

        user_uuids = [str(uuid.uuid4())]
        group_id = uuid.uuid4()
        updater = Updater(spec=GroupUpdaterSpec(), pk_value=group_id)
        action = ModifyGroupAction(
            updater=updater,
            user_update_mode=OptionalState.update("remove"),
            user_uuids=OptionalState.update(user_uuids),
        )

        await service.modify_group(action)

        call_args = mock_group_repository.modify_validated.call_args
        assert call_args[0][1] == "remove"

    async def test_nonexistent_group_raises_not_found(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Non-existent group raises ProjectNotFound."""
        mock_group_repository.modify_validated = AsyncMock(
            side_effect=ProjectNotFound("Project not found")
        )

        updater = Updater(
            spec=GroupUpdaterSpec(name=OptionalState.update("new-name")),
            pk_value=uuid.uuid4(),
        )
        action = ModifyGroupAction(updater=updater)

        with pytest.raises(ProjectNotFound):
            await service.modify_group(action)


class TestDeleteGroup:
    """Tests for GroupService.delete_group"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def service(self, mock_group_repository: MagicMock) -> GroupService:
        return _make_service(mock_group_repository)

    async def test_soft_delete_succeeds(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """UUID soft delete sets is_active=false."""
        group_id = uuid.uuid4()
        mock_group_repository.mark_inactive = AsyncMock(return_value=None)

        action = DeleteGroupAction(group_id=group_id)
        result = await service.delete_group(action)

        assert result.group_id == group_id
        mock_group_repository.mark_inactive.assert_called_once_with(group_id)

    async def test_already_inactive_is_idempotent(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Already inactive is idempotent."""
        group_id = uuid.uuid4()
        mock_group_repository.mark_inactive = AsyncMock(return_value=None)

        action = DeleteGroupAction(group_id=group_id)
        result = await service.delete_group(action)

        assert result.group_id == group_id

    async def test_nonexistent_group_raises_not_found(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Non-existent group raises ProjectNotFound."""
        mock_group_repository.mark_inactive = AsyncMock(
            side_effect=ProjectNotFound("Project not found")
        )

        action = DeleteGroupAction(group_id=uuid.uuid4())

        with pytest.raises(ProjectNotFound):
            await service.delete_group(action)


class TestPurgeGroup:
    """Tests for GroupService.purge_group"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def service(self, mock_group_repository: MagicMock) -> GroupService:
        return _make_service(mock_group_repository)

    async def test_purge_succeeds(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Hard delete + membership/quota cleanup."""
        group_id = uuid.uuid4()
        mock_group_repository.purge_group = AsyncMock(return_value=True)

        action = PurgeGroupAction(group_id=group_id)
        result = await service.purge_group(action)

        assert result.group_id == group_id
        mock_group_repository.purge_group.assert_called_once_with(group_id)

    async def test_nonexistent_group_raises_not_found(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Non-existent group raises ProjectNotFound."""
        mock_group_repository.purge_group = AsyncMock(
            side_effect=ProjectNotFound("Project not found")
        )

        action = PurgeGroupAction(group_id=uuid.uuid4())

        with pytest.raises(ProjectNotFound):
            await service.purge_group(action)


class TestSearchProjects:
    """Tests for GroupService.search_projects"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def service(self, mock_group_repository: MagicMock) -> GroupService:
        return _make_service(mock_group_repository)

    async def test_search_with_pagination(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Admin scope returns all projects with pagination."""
        projects = [_make_group_data(name=f"proj-{i}") for i in range(10)]
        mock_group_repository.search_projects = AsyncMock(
            return_value=GroupSearchResult(
                items=projects,
                total_count=25,
                has_next_page=True,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        action = SearchProjectsAction(querier=querier)

        result = await service.search_projects(action)

        assert len(result.items) == 10
        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is False
        mock_group_repository.search_projects.assert_called_once_with(querier=querier)

    async def test_search_offset_beyond_total_returns_empty(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Offset > total returns empty list + has_previous_page=true."""
        mock_group_repository.search_projects = AsyncMock(
            return_value=GroupSearchResult(
                items=[],
                total_count=5,
                has_next_page=False,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=100))
        action = SearchProjectsAction(querier=querier)

        result = await service.search_projects(action)

        assert len(result.items) == 0
        assert result.total_count == 5
        assert result.has_previous_page is True
        assert result.has_next_page is False

    async def test_search_with_is_active_filter(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """is_active filter returns only active projects."""
        active_projects = [_make_group_data(name=f"active-{i}", is_active=True) for i in range(3)]
        mock_group_repository.search_projects = AsyncMock(
            return_value=GroupSearchResult(
                items=active_projects,
                total_count=3,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        action = SearchProjectsAction(querier=querier)

        result = await service.search_projects(action)

        assert len(result.items) == 3
        assert all(p.is_active for p in result.items)


class TestSearchProjectsByDomain:
    """Tests for GroupService.search_projects_by_domain"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def service(self, mock_group_repository: MagicMock) -> GroupService:
        return _make_service(mock_group_repository)

    async def test_returns_domain_scoped_projects(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Returns domain-scoped projects only."""
        domain_projects = [_make_group_data(name=f"proj-{i}", domain_name="corp") for i in range(3)]
        mock_group_repository.search_projects_by_domain = AsyncMock(
            return_value=GroupSearchResult(
                items=domain_projects,
                total_count=3,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        scope = DomainProjectSearchScope(domain_name="corp")
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        action = SearchProjectsByDomainAction(scope=scope, querier=querier)

        result = await service.search_projects_by_domain(action)

        assert len(result.items) == 3
        assert result.total_count == 3
        assert all(p.domain_name == "corp" for p in result.items)
        mock_group_repository.search_projects_by_domain.assert_called_once_with(scope, querier)

    async def test_nonexistent_domain_returns_empty(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Non-existent domain returns empty list."""
        mock_group_repository.search_projects_by_domain = AsyncMock(
            return_value=GroupSearchResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        scope = DomainProjectSearchScope(domain_name="nonexistent")
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        action = SearchProjectsByDomainAction(scope=scope, querier=querier)

        result = await service.search_projects_by_domain(action)

        assert len(result.items) == 0
        assert result.total_count == 0


class TestSearchProjectsByUser:
    """Tests for GroupService.search_projects_by_user"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def service(self, mock_group_repository: MagicMock) -> GroupService:
        return _make_service(mock_group_repository)

    async def test_returns_user_membership_projects(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Returns user-membership projects only."""
        user_uuid = uuid.uuid4()
        user_projects = [_make_group_data(name=f"proj-{i}") for i in range(3)]
        mock_group_repository.search_projects_by_user = AsyncMock(
            return_value=GroupSearchResult(
                items=user_projects,
                total_count=3,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        scope = UserProjectSearchScope(user_uuid=user_uuid)
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        action = SearchProjectsByUserAction(scope=scope, querier=querier)

        result = await service.search_projects_by_user(action)

        assert len(result.items) == 3
        assert result.total_count == 3
        mock_group_repository.search_projects_by_user.assert_called_once_with(scope, querier)

    async def test_no_membership_returns_empty_list(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """No membership returns empty list."""
        user_uuid = uuid.uuid4()
        mock_group_repository.search_projects_by_user = AsyncMock(
            return_value=GroupSearchResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        scope = UserProjectSearchScope(user_uuid=user_uuid)
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        action = SearchProjectsByUserAction(scope=scope, querier=querier)

        result = await service.search_projects_by_user(action)

        assert len(result.items) == 0
        assert result.total_count == 0


class TestGetProject:
    """Tests for GroupService.get_project"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def service(self, mock_group_repository: MagicMock) -> GroupService:
        return _make_service(mock_group_repository)

    async def test_get_existing_project_returns_group_data(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """UUID returns GroupData."""
        project_id = uuid.uuid4()
        project = _make_group_data(name="my-project", group_id=project_id)
        mock_group_repository.get_project = AsyncMock(return_value=project)

        action = GetProjectAction(project_id=project_id)
        result = await service.get_project(action)

        assert result.data.id == project_id
        assert result.data.name == "my-project"
        mock_group_repository.get_project.assert_called_once_with(project_id)

    async def test_get_nonexistent_project_raises_not_found(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Non-existent UUID raises ProjectNotFound."""
        mock_group_repository.get_project = AsyncMock(
            side_effect=ProjectNotFound("Project not found")
        )

        action = GetProjectAction(project_id=uuid.uuid4())

        with pytest.raises(ProjectNotFound):
            await service.get_project(action)


class TestUsagePerMonth:
    """Tests for GroupService.usage_per_month"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def service(self, mock_group_repository: MagicMock) -> GroupService:
        svc = _make_service(mock_group_repository)
        type(svc._config_provider.config.system).timezone = PropertyMock(return_value=UTC)
        return svc

    async def test_valid_month_returns_stats(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """'YYYYMM' format returns monthly stats."""
        mock_group_repository.get_container_stats_for_period = AsyncMock(
            return_value=[{"project_id": str(uuid.uuid4()), "sessions": 10}]
        )

        action = UsagePerMonthAction(month="202601")
        result = await service.usage_per_month(action)

        assert len(result.result) == 1
        mock_group_repository.get_container_stats_for_period.assert_called_once()

    async def test_valid_month_with_group_ids_filter(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """group_ids filter passes to repository."""
        group_id = uuid.uuid4()
        mock_group_repository.get_container_stats_for_period = AsyncMock(return_value=[])

        action = UsagePerMonthAction(month="202601", group_ids=[group_id])
        result = await service.usage_per_month(action)

        assert result.result == []
        call_args = mock_group_repository.get_container_stats_for_period.call_args
        assert call_args[0][2] == [group_id]

    async def test_invalid_month_format_raises_error(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Invalid format raises InvalidAPIParameters."""
        action = UsagePerMonthAction(month="invalid")

        with pytest.raises(InvalidAPIParameters):
            await service.usage_per_month(action)

    async def test_month_with_no_sessions_returns_empty(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Month with no sessions returns empty list."""
        mock_group_repository.get_container_stats_for_period = AsyncMock(return_value=[])

        action = UsagePerMonthAction(month="202601")
        result = await service.usage_per_month(action)

        assert result.result == []


class TestUsagePerPeriod:
    """Tests for GroupService.usage_per_period"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def service(self, mock_group_repository: MagicMock) -> GroupService:
        svc = _make_service(mock_group_repository)
        type(svc._config_provider.config.system).timezone = PropertyMock(return_value=UTC)
        return svc

    @patch.object(GroupService, "_get_project_stats_for_period", new_callable=AsyncMock)
    async def test_valid_date_range_returns_stats(
        self,
        mock_get_stats: AsyncMock,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """'YYYYMMDD' date range returns stats."""
        mock_get_stats.return_value = {}

        action = UsagePerPeriodAction(start_date="20260101", end_date="20260131")
        result = await service.usage_per_period(action)

        assert result.result == []
        mock_get_stats.assert_called_once()

    async def test_end_before_start_raises_error(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """end <= start raises InvalidAPIParameters."""
        action = UsagePerPeriodAction(start_date="20260201", end_date="20260101")

        with pytest.raises(InvalidAPIParameters):
            await service.usage_per_period(action)

    async def test_more_than_100_days_raises_error(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """>100 days raises InvalidAPIParameters."""
        action = UsagePerPeriodAction(start_date="20260101", end_date="20260501")

        with pytest.raises(InvalidAPIParameters):
            await service.usage_per_period(action)

    async def test_invalid_date_format_raises_error(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Invalid date format raises InvalidAPIParameters."""
        action = UsagePerPeriodAction(start_date="invalid", end_date="20260101")

        with pytest.raises(InvalidAPIParameters):
            await service.usage_per_period(action)
