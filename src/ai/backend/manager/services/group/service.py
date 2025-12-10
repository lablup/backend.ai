import logging
from datetime import datetime, timedelta
from typing import Optional, Sequence
from uuid import UUID

from dateutil.relativedelta import relativedelta

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.exception import (
    InvalidAPIParameters,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.resource_usage import (
    ProjectResourceUsage,
    parse_resource_usage_groups,
    parse_total_resource_group,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.group.admin_repository import AdminGroupRepository
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.services.group.actions.create_group import (
    CreateGroupAction,
    CreateGroupActionResult,
)
from ai.backend.manager.services.group.actions.delete_group import (
    DeleteGroupAction,
    DeleteGroupActionResult,
)
from ai.backend.manager.services.group.actions.modify_group import (
    ModifyGroupAction,
    ModifyGroupActionResult,
)
from ai.backend.manager.services.group.actions.purge_group import (
    PurgeGroupAction,
    PurgeGroupActionResult,
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
    _admin_group_repository: AdminGroupRepository

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
        self._admin_group_repository = group_repositories.admin_repository

    async def create_group(self, action: CreateGroupAction) -> CreateGroupActionResult:
        group_data = await self._group_repository.create(action.input)
        return CreateGroupActionResult(data=group_data)

    async def modify_group(self, action: ModifyGroupAction) -> ModifyGroupActionResult:
        from ai.backend.manager.models.user import UserRole

        # Convert user_uuids from list[str] to list[UUID] if provided
        user_uuids_converted = None
        user_uuids_list = action.user_uuids.optional_value()
        if user_uuids_list:
            user_uuids_converted = [UUID(user_uuid) for user_uuid in user_uuids_list]

        group_data = await self._group_repository.modify_validated(
            action.group_id,
            action.modifier,
            UserRole.USER,  # Default role since group operations don't require role-based logic
            action.user_update_mode.optional_value(),
            user_uuids_converted,
        )
        # If no group data is returned, it means only user updates were performed
        return ModifyGroupActionResult(data=group_data)

    async def delete_group(self, action: DeleteGroupAction) -> DeleteGroupActionResult:
        await self._group_repository.mark_inactive(action.group_id)
        return DeleteGroupActionResult(group_id=action.group_id)

    async def purge_group(self, action: PurgeGroupAction) -> PurgeGroupActionResult:
        await self._admin_group_repository.purge_group_force(action.group_id)
        return PurgeGroupActionResult(group_id=action.group_id)

    async def _get_project_stats_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        project_ids: Optional[Sequence[UUID]] = None,
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
        except ValueError:
            raise InvalidAPIParameters(extra_msg="Invalid date values")
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
        except ValueError:
            raise InvalidAPIParameters(extra_msg="Invalid date values")
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
