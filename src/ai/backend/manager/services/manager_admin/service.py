from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.manager.data.manager_status.types import ManagerStatus
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.resource import InstanceNotFound
from ai.backend.manager.repositories.manager_admin.health import get_manager_db_cxn_status

from .actions.fetch_status import FetchManagerStatusAction, FetchManagerStatusActionResult
from .actions.get_announcement import GetAnnouncementAction, GetAnnouncementActionResult
from .actions.get_db_cxn_status import GetDbCxnStatusAction, GetDbCxnStatusActionResult
from .actions.perform_scheduler_ops import (
    PerformSchedulerOpsAction,
    PerformSchedulerOpsActionResult,
)
from .actions.update_announcement import UpdateAnnouncementAction, UpdateAnnouncementActionResult
from .actions.update_status import UpdateManagerStatusAction, UpdateManagerStatusActionResult

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
    from ai.backend.manager.repositories.manager_admin import ManagerAdminRepository

__all__ = ("ManagerAdminService",)

# etcd keys backing the system announcement. The message and the enabled flag
# are stored under separate subpaths of ``manager/announcement`` so that
# disabling an announcement only flips the flag and keeps the stored message
# (re-enabling does not require retyping). Older deployments stored a bare
# message string directly at ``manager/announcement``; ``get_announcement``
# reads each subpath on its own and falls back to that legacy key for whichever
# one is absent, and the first write migrates to the split layout.
_ANNOUNCEMENT_KEY = "manager/announcement"
_ANNOUNCEMENT_MESSAGE_KEY = "manager/announcement/message"
_ANNOUNCEMENT_ENABLED_KEY = "manager/announcement/enabled"


@dataclass
class ManagerAdminService:
    """Service for manager administration operations."""

    _repository: ManagerAdminRepository
    _config_provider: ManagerConfigProvider
    _etcd: AsyncEtcd
    _db: ExtendedAsyncSAEngine
    _valkey_stat: ValkeyStatClient

    def __init__(
        self,
        *,
        repository: ManagerAdminRepository,
        config_provider: ManagerConfigProvider,
        etcd: AsyncEtcd,
        db: ExtendedAsyncSAEngine,
        valkey_stat: ValkeyStatClient,
    ) -> None:
        self._repository = repository
        self._config_provider = config_provider
        self._etcd = etcd
        self._db = db
        self._valkey_stat = valkey_stat

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
        """Get the current announcement from etcd.

        Each subpath key is read on its own; whichever one is absent falls back
        to the legacy single key, whose bare presence denotes an enabled
        announcement. Absent everywhere means "no announcement".
        """
        message = await self._etcd.get(_ANNOUNCEMENT_MESSAGE_KEY)
        enabled_flag = await self._etcd.get(_ANNOUNCEMENT_ENABLED_KEY)
        if message is None or enabled_flag is None:
            legacy_message = await self._etcd.get(_ANNOUNCEMENT_KEY)
            if message is None:
                message = legacy_message
            if enabled_flag is None:
                enabled_flag = "true" if legacy_message is not None else "false"
        return GetAnnouncementActionResult(enabled=enabled_flag == "true", message=message or "")

    async def update_announcement(
        self, action: UpdateAnnouncementAction
    ) -> UpdateAnnouncementActionResult:
        """Update the announcement in etcd.

        The message is retained across enable/disable: disabling only flips the
        enabled flag and keeps the stored message, so re-enabling does not
        require retyping it. Enabling still requires a non-empty message; pass an
        explicit empty message to clear the stored text.
        """
        if action.enabled and not action.message:
            raise InvalidAPIParameters(extra_msg="Empty message not allowed to enable announcement")
        # A request without a message (e.g. a plain disable) preserves the
        # existing text, so read the current message before rewriting the keys.
        if action.message is None:
            current = await self.get_announcement(GetAnnouncementAction())
            message = current.message
        else:
            message = action.message
        # Replace the whole announcement subtree in a single transaction: the two
        # subpath keys are written and every other key under the prefix is
        # removed, so the legacy single key (superseded by the split keys) is
        # dropped as part of the same write rather than in a separate step.
        await self._etcd.atomic_replace_prefixes({
            _ANNOUNCEMENT_KEY: {
                "message": message,
                "enabled": "true" if action.enabled else "false",
            },
        })
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

    async def get_db_cxn_status(self, action: GetDbCxnStatusAction) -> GetDbCxnStatusActionResult:
        """Get database connection status from all manager processes."""
        cxn_infos = await get_manager_db_cxn_status(
            self._valkey_stat, self._db, self._config_provider
        )
        return GetDbCxnStatusActionResult(cxn_infos=cxn_infos)
