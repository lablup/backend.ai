from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from typing import Mapping, Optional

import aiotools
from sqlalchemy import and_

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.metrics.metric import SweeperMetricObserver
from ai.backend.common.stage.types import Provisioner
from ai.backend.common.validators import TimeDelta
from ai.backend.manager.config_legacy import kernel_hang_tolerance_iv, session_hang_tolerance_iv
from ai.backend.manager.models.session import SessionStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.setup.core.agent_registry import AgentRegistryResource
from ai.backend.manager.sweeper.base import DEFAULT_SWEEP_INTERVAL_SEC
from ai.backend.manager.sweeper.kernel import KernelSweeper
from ai.backend.manager.sweeper.session import SessionSweeper


@dataclass
class SweeperTask:
    task: asyncio.Task[None]
    
    async def cancel(self) -> None:
        if not self.task.done():
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task


@dataclass
class StaleSessionSweeperSpec:
    etcd: AsyncEtcd
    database: ExtendedAsyncSAEngine
    agent_registry_resource: AgentRegistryResource
    sweeper_metric: SweeperMetricObserver


class StaleSessionSweeperProvisioner(Provisioner[StaleSessionSweeperSpec, SweeperTask]):
    @property
    def name(self) -> str:
        return "stale_session_sweeper"

    async def setup(self, spec: StaleSessionSweeperSpec) -> SweeperTask:
        # TODO: Resolve type issue and, Use `session_hang_tolerance` from the unified config
        session_hang_tolerance = session_hang_tolerance_iv.check(
            await spec.etcd.get_prefix_dict("config/session/hang-tolerance")
        )
        status_threshold_map: dict[SessionStatus, TimeDelta] = {}
        for status, threshold in session_hang_tolerance["threshold"].items():
            try:
                status_threshold_map[SessionStatus(status)] = threshold
            except ValueError:
                # log.warning("sweep(session) - Skipping invalid session status '{}'.", status)
                pass

        async def _sweep(interval: float) -> None:
            await SessionSweeper(
                spec.database,
                spec.agent_registry_resource.registry,
                spec.sweeper_metric,
                status_threshold_map=status_threshold_map,
            ).sweep()

        task = aiotools.create_timer(_sweep, interval=DEFAULT_SWEEP_INTERVAL_SEC)
        return SweeperTask(task=task)

    async def teardown(self, resource: SweeperTask) -> None:
        await resource.cancel()


@dataclass
class StaleKernelSweeperSpec:
    etcd: AsyncEtcd
    database: ExtendedAsyncSAEngine
    agent_registry_resource: AgentRegistryResource
    sweeper_metric: SweeperMetricObserver


class StaleKernelSweeperProvisioner(Provisioner[StaleKernelSweeperSpec, SweeperTask]):
    @property
    def name(self) -> str:
        return "stale_kernel_sweeper"

    async def setup(self, spec: StaleKernelSweeperSpec) -> SweeperTask:
        # TODO: Resolve type issue and, Use `kernel_hang_tolerance` from the unified config
        kernel_hang_tolerance = kernel_hang_tolerance_iv.check(
            await spec.etcd.get_prefix_dict("config/kernel/hang-tolerance")
        )

        async def _sweep(interval: float) -> None:
            await KernelSweeper(
                spec.database,
                spec.agent_registry_resource.registry,
                spec.sweeper_metric,
                duration_threshold=kernel_hang_tolerance["threshold"],
            ).sweep()

        task = aiotools.create_timer(_sweep, interval=DEFAULT_SWEEP_INTERVAL_SEC)
        return SweeperTask(task=task)

    async def teardown(self, resource: SweeperTask) -> None:
        await resource.cancel()