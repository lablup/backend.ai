from __future__ import annotations

import asyncio
import contextlib
import logging
import random
import time
from dataclasses import dataclass

from ai.backend.appproxy.common.errors import WorkerNotAvailable
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
    healthy target of that group evenly. TCP connect probes run in the background and flip
    targets between healthy and unhealthy; a target that stays unreachable for
    ``recovery_timeout`` is evicted.

    :meth:`update` applies a new Ingress backend:

    - a target with a new id, or a known id at a new address or session → a fresh health state
    - a target missing from the update → dropped
    - a known id at the same address and session → keeps its health state
    """

    _ingress_backend: IngressBackend
    _target_by_id: dict[IngressTargetID, IngressTarget]
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
        self._target_by_id = {target.id: target for target in self._targets_of(ingress_backend)}
        self._health_by_target_id = {target_id: _TargetHealth() for target_id in self._target_by_id}
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
            target_by_id = {target.id: target for target in self._targets_of(ingress_backend)}
            health_by_target_id: dict[IngressTargetID, _TargetHealth] = {}
            for target_id, target in target_by_id.items():
                health = self._health_by_target_id.get(target_id)
                if health is None or self._target_by_id.get(target_id) != target:
                    health = _TargetHealth()
                health_by_target_id[target_id] = health
            self._ingress_backend = ingress_backend
            self._target_by_id = target_by_id
            self._health_by_target_id = health_by_target_id

    async def select(self) -> IngressTarget:
        async with self._lock:
            healthy_targets_by_group: list[tuple[int, list[IngressTarget]]] = []
            for target_group in self._ingress_backend.target_groups:
                if target_group.weight <= 0:
                    continue
                healthy_targets = [
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
        if self._target_by_id.get(target.id) != target:
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
                await asyncio.sleep(self._spec.health_check_interval)
                try:
                    await self._probe_all_targets()
                except Exception:
                    log.exception("target health check failed")
        except asyncio.CancelledError:
            raise

    async def _probe_all_targets(self) -> None:
        async with self._lock:
            targets_with_health = [
                (target, health)
                for target in self._targets_of(self._ingress_backend)
                if (health := self._health_by_target_id.get(target.id)) is not None
            ]
        if not targets_with_health:
            return
        await asyncio.gather(
            *(self._probe_target(target, health) for target, health in targets_with_health),
            return_exceptions=True,
        )

    async def _probe_target(self, target: IngressTarget, health: _TargetHealth) -> None:
        ok = await self._tcp_probe(target.host, target.port)
        if ok:
            if not health.is_healthy:
                log.debug("target recovered", target_id=target.id)
            health.is_healthy = True
            health.failure_count = 0
            health.unhealthy_since = None
            return
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
                        "unreachable target evicted",
                        target_id=target.id,
                        recovery_timeout_sec=self._spec.recovery_timeout,
                    )

    async def _tcp_probe(self, host: str, port: int) -> bool:
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
