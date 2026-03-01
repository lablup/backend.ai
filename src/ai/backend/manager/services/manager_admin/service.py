from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.resource import InstanceNotFound

from .actions.fetch_status import FetchManagerStatusAction, FetchManagerStatusActionResult
from .actions.get_announcement import GetAnnouncementAction, GetAnnouncementActionResult
from .actions.perform_scheduler_ops import (
    PerformSchedulerOpsAction,
    PerformSchedulerOpsActionResult,
)
from .actions.update_announcement import UpdateAnnouncementAction, UpdateAnnouncementActionResult
from .actions.update_status import UpdateManagerStatusAction, UpdateManagerStatusActionResult

if TYPE_CHECKING:
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.repositories.manager_admin import ManagerAdminRepository

__all__ = ("ManagerAdminService",)


@dataclass
class ManagerAdminService:
    """Service for manager administration operations."""

    _repository: ManagerAdminRepository
    _config_provider: ManagerConfigProvider
    _etcd: AsyncEtcd

    def __init__(
        self,
        *,
        repository: ManagerAdminRepository,
        config_provider: ManagerConfigProvider,
        etcd: AsyncEtcd,
    ) -> None:
        self._repository = repository
        self._config_provider = config_provider
        self._etcd = etcd

    async def fetch_status(
        self, action: FetchManagerStatusAction
    ) -> FetchManagerStatusActionResult:
        """Fetch the current manager status including active session count."""
        status = await self._config_provider.legacy_etcd_config_loader.get_manager_status()
        active_sessions = await self._repository.count_active_sessions()
        configs = self._config_provider.config.manager
        manager_id = configs.id if configs.id else socket.gethostname()
        return FetchManagerStatusActionResult(
            status=status.value,
            active_sessions=active_sessions,
            manager_id=manager_id,
            num_proc=configs.num_proc,
            service_addr=str(configs.service_addr),
            heartbeat_timeout=configs.heartbeat_timeout,
            ssl_enabled=configs.ssl_enabled,
        )

    async def update_status(
        self, action: UpdateManagerStatusAction
    ) -> UpdateManagerStatusActionResult:
        """Update the manager status in etcd."""
        status = ManagerStatus(action.status)
        await self._config_provider.legacy_etcd_config_loader.update_manager_status(status)
        return UpdateManagerStatusActionResult()

    async def get_announcement(self, action: GetAnnouncementAction) -> GetAnnouncementActionResult:
        """Get the current announcement from etcd."""
        data = await self._etcd.get("manager/announcement")
        if data is None:
            return GetAnnouncementActionResult(enabled=False, message="")
        return GetAnnouncementActionResult(enabled=True, message=data)

    async def update_announcement(
        self, action: UpdateAnnouncementAction
    ) -> UpdateAnnouncementActionResult:
        """Update the announcement in etcd."""
        if action.enabled:
            if not action.message:
                raise InvalidAPIParameters(
                    extra_msg="Empty message not allowed to enable announcement"
                )
            await self._etcd.put("manager/announcement", action.message)
        else:
            await self._etcd.delete("manager/announcement")
        return UpdateAnnouncementActionResult()

    async def perform_scheduler_ops(
        self, action: PerformSchedulerOpsAction
    ) -> PerformSchedulerOpsActionResult:
        """Perform a scheduler operation (include/exclude agents)."""
        rowcount = await self._repository.update_agent_schedulable(
            action.agent_ids, action.schedulable
        )
        if rowcount < len(action.agent_ids):
            raise InstanceNotFound()
        return PerformSchedulerOpsActionResult()
