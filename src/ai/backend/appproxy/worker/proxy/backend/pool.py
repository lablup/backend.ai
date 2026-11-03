from __future__ import annotations

import asyncio
import contextlib
import logging
import random
import time
from dataclasses import dataclass

import aiohttp

from ai.backend.appproxy.common.errors import WorkerNotAvailable
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    IngressBackend,
    IngressTarget,
    IngressTargetID,
)
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass(slots=True)
class _TargetHealth:
    """Health state of a target, kept while the target keeps its id and address."""

    is_healthy: bool = True
    failure_count: int = 0
    consecutive_http_probe_failures: int = 0
    unhealthy_since: float | None = None


@dataclass(slots=True)
class RoutePoolSpec:
    """Runtime tunables for a per-backend :class:`RoutePool`."""

    failure_threshold: int = 3
    health_check_interval: float = 10.0
    connect_timeout: float = 1.0
    recovery_timeout: float = 60.0


class RoutePool:
    """Health-checked targets of an Ingress backend.

    Selection picks a target group by weight among the groups with a healthy target, then a
    healthy target of that group evenly. Probes run in the background and flip targets between
    healthy and unhealthy: an HTTP GET by the Ingress backend's health check when it is enabled,
    a TCP connect otherwise. A target that stays unhealthy for ``recovery_timeout`` is evicted.

    :meth:`update` applies a new Ingress backend:

    - a target with a new id, or a known id at a new address → a fresh health state
    - a target missing from the update → dropped
    - a known id at the same address → keeps its health state
    """

    _ingress_backend: IngressBackend
    _health_by_target_id: dict[IngressTargetID, _TargetHealth]
    _lock: asyncio.Lock
    _health_check_task: asyncio.Task[None] | None
    _spec: RoutePoolSpec
    _no_healthy_target: bool

    def __init__(
        self,
        ingress_backend: IngressBackend,
        *,
        spec: RoutePoolSpec | None = None,
    ) -> None:
        self._ingress_backend = ingress_backend
        self._health_by_target_id = {
            target.id: _TargetHealth() for target in self._targets_of(ingress_backend)
        }
        self._lock = asyncio.Lock()
        self._spec = spec or RoutePoolSpec()
        self._no_healthy_target = False
        self._health_check_task = asyncio.create_task(
            self._health_check_loop(),
            name="RoutePool._health_check_loop",
        )

    async def close(self) -> None:
        task = self._health_check_task
        if task is not None:
            task.cancel()
            with contextlib.suppress(BaseException):
                await task
            self._health_check_task = None

    async def update(self, ingress_backend: IngressBackend) -> None:
        async with self._lock:
            known_target_by_id = {
                target.id: target for target in self._targets_of(self._ingress_backend)
            }
            health_by_target_id: dict[IngressTargetID, _TargetHealth] = {}
            for target in self._targets_of(ingress_backend):
                health = self._health_by_target_id.get(target.id)
                if health is None or known_target_by_id.get(target.id) != target:
                    health = _TargetHealth()
                health_by_target_id[target.id] = health
            self._ingress_backend = ingress_backend
            self._health_by_target_id = health_by_target_id

    async def select(self) -> IngressTarget:
        async with self._lock:
            healthy_targets_by_group: list[tuple[int, list[IngressTarget]]] = []
            for target_group in self._ingress_backend.target_groups:
                if target_group.weight <= 0:
                    continue
                healthy_targets: list[IngressTarget] = [
                    target
                    for target in target_group.targets
                    if (health := self._health_by_target_id.get(target.id)) is not None
                    and health.is_healthy
                ]
                if healthy_targets:
                    healthy_targets_by_group.append((target_group.weight, healthy_targets))
        if not healthy_targets_by_group:
            if not self._no_healthy_target:
                self._no_healthy_target = True
                log.warning(
                    "no healthy target available", target_count=len(self._health_by_target_id)
                )
            else:
                log.trace("no healthy target available")
            raise WorkerNotAvailable
        self._no_healthy_target = False
        _, healthy_targets = random.choices(
            healthy_targets_by_group,
            weights=[weight for weight, _ in healthy_targets_by_group],
            k=1,
        )[0]
        return random.choice(healthy_targets)

    def record_failure(self, target: IngressTarget) -> None:
        health = self._health_of(target)
        if health is None:
            return
        health.failure_count += 1
        if health.failure_count >= self._spec.failure_threshold:
            if health.is_healthy:
                log.warning(
                    "target marked unhealthy after request failures",
                    target_id=target.id,
                    failure_count=health.failure_count,
                )
            health.is_healthy = False
            if health.unhealthy_since is None:
                health.unhealthy_since = time.perf_counter()

    def record_success(self, target: IngressTarget) -> None:
        health = self._health_of(target)
        if health is None:
            return
        if not health.is_healthy:
            log.debug("target recovered", target_id=target.id)
        health.failure_count = 0
        health.is_healthy = True
        health.unhealthy_since = None

    def _health_of(self, target: IngressTarget) -> _TargetHealth | None:
        if not any(target in group.targets for group in self._ingress_backend.target_groups):
            return None
        return self._health_by_target_id.get(target.id)

    @staticmethod
    def _targets_of(ingress_backend: IngressBackend) -> list[IngressTarget]:
        return [
            target
            for target_group in ingress_backend.target_groups
            for target in target_group.targets
        ]

    async def _health_check_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._probe_interval())
                try:
                    await self._probe_all_targets()
                except Exception:
                    log.exception("target health check failed")
        except asyncio.CancelledError:
            raise

    def _enabled_http_health_check(self) -> ModelHealthCheck | None:
        health_check = self._ingress_backend.health_check
        if health_check is None or not health_check.enable:
            return None
        return health_check

    def _probe_interval(self) -> float:
        http_health_check = self._enabled_http_health_check()
        if http_health_check is None:
            return self._spec.health_check_interval
        return http_health_check.interval

    async def _probe_all_targets(self) -> None:
        async with self._lock:
            targets_with_health = [
                (target, health)
                for target in self._targets_of(self._ingress_backend)
                if (health := self._health_by_target_id.get(target.id)) is not None
            ]
            http_health_check = self._enabled_http_health_check()
        if not targets_with_health:
            return
        await asyncio.gather(
            *(
                self._probe_target(target, health, http_health_check)
                for target, health in targets_with_health
            ),
            return_exceptions=True,
        )

    async def _probe_target(
        self,
        target: IngressTarget,
        health: _TargetHealth,
        http_health_check: ModelHealthCheck | None,
    ) -> None:
        if http_health_check is None:
            await self._probe_by_tcp_connect(target, health)
        else:
            await self._probe_by_http_get(target, health, http_health_check)

    async def _probe_by_tcp_connect(self, target: IngressTarget, health: _TargetHealth) -> None:
        if await self._tcp_connect_succeeds(target.host, target.port):
            self._mark_healthy_by_probe(target, health)
        else:
            await self._mark_unhealthy_by_probe_or_evict(target, health)

    async def _probe_by_http_get(
        self, target: IngressTarget, health: _TargetHealth, health_check: ModelHealthCheck
    ) -> None:
        if await self._http_get_returns_expected_status(target, health_check):
            self._mark_healthy_by_probe(target, health)
        else:
            health.consecutive_http_probe_failures += 1
            if health_check.is_retry_exhausted(health.consecutive_http_probe_failures):
                await self._mark_unhealthy_by_probe_or_evict(target, health)

    def _mark_healthy_by_probe(self, target: IngressTarget, health: _TargetHealth) -> None:
        if not health.is_healthy:
            log.debug("target recovered", target_id=target.id)
        health.is_healthy = True
        health.failure_count = 0
        health.consecutive_http_probe_failures = 0
        health.unhealthy_since = None

    async def _mark_unhealthy_by_probe_or_evict(
        self, target: IngressTarget, health: _TargetHealth
    ) -> None:
        if health.is_healthy:
            log.warning("target marked unhealthy by the health check", target_id=target.id)
        health.is_healthy = False
        if health.unhealthy_since is None:
            health.unhealthy_since = time.perf_counter()
        if (
            health.unhealthy_since is not None
            and time.perf_counter() - health.unhealthy_since > self._spec.recovery_timeout
        ):
            async with self._lock:
                if self._health_by_target_id.get(target.id) is health:
                    del self._health_by_target_id[target.id]
                    log.warning(
                        "unhealthy target evicted",
                        target_id=target.id,
                        recovery_timeout_sec=self._spec.recovery_timeout,
                    )

    @staticmethod
    async def _http_get_returns_expected_status(
        target: IngressTarget, health_check: ModelHealthCheck
    ) -> bool:
        url = f"http://{target.host}:{target.port}{health_check.path}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=health_check.max_wait_time)
                ) as response:
                    return response.status == health_check.expected_status_code
        except (aiohttp.ClientError, TimeoutError):
            return False

    async def _tcp_connect_succeeds(self, host: str, port: int) -> bool:
        try:
            _reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host=host, port=port),
                timeout=self._spec.connect_timeout,
            )
        except Exception:
            return False
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()
        return True


__all__ = (
    "RoutePool",
    "RoutePoolSpec",
)
