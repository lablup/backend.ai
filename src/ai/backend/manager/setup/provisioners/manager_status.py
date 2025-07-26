import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, override

from ai.backend.common.stage.types import Provisioner
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.config.provider import ManagerConfigProvider

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ManagerStatusSpec:
    pidx: int
    config_provider: ManagerConfigProvider


@dataclass
class ManagerStatusResult:
    status: Optional[ManagerStatus]


class ManagerStatusProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "manager-status-provisioner"

    @override
    async def setup(self, spec: ManagerStatusSpec) -> ManagerStatusResult:
        mgr_status = None
        if spec.pidx == 0:
            mgr_status = await spec.config_provider.legacy_etcd_config_loader.get_manager_status()
            if mgr_status is None or mgr_status not in (
                ManagerStatus.RUNNING,
                ManagerStatus.FROZEN,
            ):
                # legacy transition: we now have only RUNNING or FROZEN for HA setup.
                await spec.config_provider.legacy_etcd_config_loader.update_manager_status(
                    ManagerStatus.RUNNING
                )
                mgr_status = ManagerStatus.RUNNING
            log.info("Manager status: {}", mgr_status)
            tz = spec.config_provider.config.system.timezone
            log.info("Configured timezone: {}", tz.tzname(datetime.now()))
        return ManagerStatusResult(status=mgr_status)

    @override
    async def teardown(self, resource: ManagerStatusResult) -> None:
        # Nothing to clean up
        pass
