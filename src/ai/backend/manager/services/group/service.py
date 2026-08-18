from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime, timedelta
from uuid import UUID

from dateutil.relativedelta import relativedelta

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.exception import (
    InvalidAPIParameters,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.dotfile.types import DotfileEntries
from ai.backend.manager.models.domain.row import verify_dotfile_name
from ai.backend.manager.models.group.updaters import GroupDotfilesUpdater
from ai.backend.manager.models.resource_usage import (
    ProjectResourceUsage,
    parse_resource_usage_groups,
    parse_total_resource_group,
)
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.services.group.actions.assign_users_to_project import (
    AssignUsersToProjectAction,
    AssignUsersToProjectActionResult,
)
from ai.backend.manager.services.group.actions.create_project_dotfile import (
    CreateProjectDotfileAction,
    CreateProjectDotfileActionResult,
)
from ai.backend.manager.services.group.actions.delete_project_dotfile import (
    DeleteProjectDotfileAction,
    DeleteProjectDotfileActionResult,
)
from ai.backend.manager.services.group.actions.purge_group import (
    PurgeGroupAction,
    PurgeGroupActionResult,
)
from ai.backend.manager.services.group.actions.unassign_users import (
    UnassignUsersFromProjectAction,
    UnassignUsersFromProjectActionResult,
)
from ai.backend.manager.services.group.actions.update_group import (
    UpdateGroupAction,
    UpdateGroupActionResult,
)
from ai.backend.manager.services.group.actions.update_project_dotfile import (
    UpdateProjectDotfileAction,
    UpdateProjectDotfileActionResult,
)
from ai.backend.manager.services.group.actions.usage_per_month import (
    UsagePerMonthAction,
    UsagePerMonthActionResult,
)
from ai.backend.manager.services.group.actions.usage_per_period import (
    UsagePerPeriodAction,
    UsagePerPeriodActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GroupService:
    _config_provider: ManagerConfigProvider
    _valkey_stat_client: ValkeyStatClient
    _storage_manager: StorageSessionManager
    _group_repository: GroupRepository

    def __init__(
        self,
        storage_manager: StorageSessionManager,
        config_provider: ManagerConfigProvider,
        valkey_stat_client: ValkeyStatClient,
        group_repositories: GroupRepositories,
    ) -> None:
        self._storage_manager = storage_manager
        self._config_provider = config_provider
        self._valkey_stat_client = valkey_stat_client
        self._group_repository = group_repositories.repository

    async def update_group(self, action: UpdateGroupAction) -> UpdateGroupActionResult:
        # Convert user_uuids from list[str] to list[UUID] if provided
        user_uuids_converted = None
        user_uuids_list = action.user_uuids.optional_value()
        if user_uuids_list:
            user_uuids_converted = [UUID(user_uuid) for user_uuid in user_uuids_list]

        group_data = await self._group_repository.modify_validated(
            action.project_id,
            action.updater,
            action.user_update_mode.optional_value(),
            user_uuids_converted,
        )
        # If no group data is returned, it means only user updates were performed or no updates at all
        return UpdateGroupActionResult(data=group_data)

    async def purge_group(self, action: PurgeGroupAction) -> PurgeGroupActionResult:
        await self._group_repository.purge_group(action.project_id)
        return PurgeGroupActionResult(project_id=action.project_id)

    async def unassign_users_from_project(
        self, action: UnassignUsersFromProjectAction
    ) -> UnassignUsersFromProjectActionResult:
        result = await self._group_repository.unassign_users_from_project(action.unbinder)
        return UnassignUsersFromProjectActionResult(
            project_id=action.project_id,
            unassigned_users=result.unassigned_users,
            failures=result.failures,
        )

    async def _get_project_stats_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        project_ids: Sequence[UUID] | None = None,
    ) -> dict[UUID, ProjectResourceUsage]:
        kernels = await self._group_repository.fetch_project_resource_usage(
            start_date, end_date, project_ids=project_ids
        )
        local_tz = self._config_provider.config.system.timezone
        usage_groups = await parse_resource_usage_groups(
            kernels, self._valkey_stat_client, local_tz
        )
        total_groups, _ = parse_total_resource_group(usage_groups)
        return total_groups

    # group (or all the groups)
    async def usage_per_month(self, action: UsagePerMonthAction) -> UsagePerMonthActionResult:
        month = action.month
        local_tz = self._config_provider.config.system.timezone

        try:
            start_date = datetime.strptime(month, "%Y%m").replace(tzinfo=local_tz)
            end_date = start_date + relativedelta(months=+1)
        except ValueError as e:
            raise InvalidAPIParameters(extra_msg="Invalid date values") from e
        result = await self._group_repository.get_container_stats_for_period(
            start_date, end_date, action.group_ids
        )
        log.debug("container list are retrieved for month {0}", month)
        return UsagePerMonthActionResult(result=result)

    # group (or all the groups)
    async def usage_per_period(self, action: UsagePerPeriodAction) -> UsagePerPeriodActionResult:
        local_tz = self._config_provider.config.system.timezone
        project_id = action.project_id

        try:
            start_date = datetime.strptime(action.start_date, "%Y%m%d").replace(tzinfo=local_tz)
            end_date = datetime.strptime(action.end_date, "%Y%m%d").replace(tzinfo=local_tz)
            end_date = end_date + timedelta(days=1)  # include sessions in end_date
            if end_date - start_date > timedelta(days=100):
                raise InvalidAPIParameters("Cannot query more than 100 days")
        except ValueError as e:
            raise InvalidAPIParameters(extra_msg="Invalid date values") from e
        if end_date <= start_date:
            raise InvalidAPIParameters(extra_msg="end_date must be later than start_date.")
        log.info(
            "USAGE_PER_MONTH (p:{}, start_date:{}, end_date:{})", project_id, start_date, end_date
        )
        project_ids = [project_id] if project_id is not None else None
        usage_map = await self._get_project_stats_for_period(
            start_date, end_date, project_ids=project_ids
        )
        result = [p_usage.to_json(child=True) for p_usage in usage_map.values()]
        log.debug("container list are retrieved from {0} to {1}", start_date, end_date)
        return UsagePerPeriodActionResult(result=result)

    async def assign_users_to_project(
        self, action: AssignUsersToProjectAction
    ) -> AssignUsersToProjectActionResult:
        assigned_users = await self._group_repository.assign_users_to_project(
            action.project_id, action.user_ids, action.role_id
        )
        return AssignUsersToProjectActionResult(
            project_id=action.project_id, assigned_users=assigned_users
        )

    async def create_dotfile(
        self, action: CreateProjectDotfileAction
    ) -> CreateProjectDotfileActionResult:
        if not verify_dotfile_name(action.entry.path):
            raise InvalidAPIParameters("dotfile path is reserved for internal operations.")
        entries = (await self._read_dotfiles(action.project_id)).added(action.entry)
        await self._write_dotfiles(action.project_id, entries)
        return CreateProjectDotfileActionResult(entries=entries.entries)

    async def update_dotfile(
        self, action: UpdateProjectDotfileAction
    ) -> UpdateProjectDotfileActionResult:
        entries = (await self._read_dotfiles(action.project_id)).replaced(action.entry)
        await self._write_dotfiles(action.project_id, entries)
        return UpdateProjectDotfileActionResult(entries=entries.entries)

    async def delete_dotfile(
        self, action: DeleteProjectDotfileAction
    ) -> DeleteProjectDotfileActionResult:
        entries = (await self._read_dotfiles(action.project_id)).removed(action.path)
        await self._write_dotfiles(action.project_id, entries)
        return DeleteProjectDotfileActionResult(entries=entries.entries)

    async def _read_dotfiles(self, project_id: ProjectID) -> DotfileEntries:
        data = await self._group_repository.get_project(project_id)
        return DotfileEntries.unpack(data.dotfiles)

    async def _write_dotfiles(self, project_id: ProjectID, entries: DotfileEntries) -> None:
        await self._group_repository.update_dotfiles(
            GroupDotfilesUpdater(project_id=project_id, dotfiles=entries.pack())
        )
