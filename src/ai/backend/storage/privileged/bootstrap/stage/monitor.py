import asyncio
import logging
import os
from dataclasses import dataclass
from typing import override

import aiomonitor

from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.metrics.profiler import Profiler, PyroscopeArgs
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.logging import BraceStyleAdapter

from ...config import StorageProxyPrivilegedWorkerConfig

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class MonitorSpec:
    local_config: StorageProxyPrivilegedWorkerConfig
    loop: asyncio.AbstractEventLoop
    pidx: int


class MonitorSpecGenerator(ArgsSpecGenerator[MonitorSpec]):
    pass


@dataclass
class MonitorResult:
    aiomonitor_started: bool
    aiomonitor: aiomonitor.Monitor
    metric_registry: CommonMetricRegistry


class MonitorProvisioner(Provisioner[MonitorSpec, MonitorResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-monitor"

    @override
    async def setup(self, spec: MonitorSpec) -> MonitorResult:
        local_config = spec.local_config
        m = aiomonitor.Monitor(
            spec.loop,
            termui_port=local_config.storage_proxy.aiomonitor_termui_port + spec.pidx,
            webui_port=local_config.storage_proxy.aiomonitor_webui_port + spec.pidx,
            console_enabled=False,
            hook_task_factory=local_config.debug.enhanced_aiomonitor_task_info,
        )
        Profiler(
            pyroscope_args=PyroscopeArgs(
                enabled=local_config.pyroscope.enabled,
                application_name=local_config.pyroscope.app_name,
                server_address=local_config.pyroscope.server_addr,
                sample_rate=local_config.pyroscope.sample_rate,
            )
        )
        m.prompt = f"monitor (storage-proxy[{spec.pidx}@{os.getpid()}]) >>> "
        m.console_locals["local_config"] = local_config
        aiomon_started = False
        try:
            m.start()
            aiomon_started = True
        except Exception as e:
            log.warning(
                "aiomonitor could not start but skipping this error to continue", exc_info=e
            )
        metric_registry = CommonMetricRegistry()
        return MonitorResult(aiomon_started, m, metric_registry)

    @override
    async def teardown(self, resource: MonitorResult) -> None:
        if resource.aiomonitor_started:
            resource.aiomonitor.close()


class MonitorStage(ProvisionStage[MonitorSpec, MonitorResult]):
    pass
