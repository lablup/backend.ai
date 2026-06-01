from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from aiotools import cancel_and_wait

from ai.backend.common.dto.internal.health import (
    ComponentConnectivityStatus,
    ConnectivityCheckResponse,
)
from ai.backend.logging.utils import BraceStyleAdapter

from .abc import ServiceHealthChecker
from .exceptions import HealthCheckerAlreadyRegistered
from .types import AllServicesHealth, ProbeKind, ServiceGroup, ServiceHealth

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class HealthProbeOptions:
    check_interval: float = 60.0


class HealthProbe:
    """
    Probe for running periodic health checks on registered service groups.

    Checkers are tagged at registration time as liveness, readiness, or
    informational. The probe exposes a per-kind connectivity view to mirror
    Kubernetes liveness/readiness probes:

    - Liveness view: only liveness checkers gate `overall_healthy`.
    - Readiness view: liveness + readiness checkers gate (a process that is
      not alive cannot be ready).
    - Detail view (`get_connectivity_status`): every registered checker
      appears, including informational ones. `overall_healthy` here reflects
      the full surface — informational failures degrade the detail view
      without affecting the liveness or readiness probes.
    """

    _liveness: set[ServiceHealthChecker]
    _readiness: set[ServiceHealthChecker]
    _informational: set[ServiceHealthChecker]
    _results: dict[ServiceGroup, ServiceHealth]
    _loop_task: asyncio.Task[Any] | None
    _running: bool
    _options: HealthProbeOptions

    def __init__(self, options: HealthProbeOptions) -> None:
        self._liveness = set()
        self._readiness = set()
        self._informational = set()
        self._results = {}
        self._loop_task = None
        self._running = False
        self._options = options

    async def start(self) -> None:
        if self._running:
            log.warning("Health probe is already running")
            return
        self._running = True
        self._loop_task = asyncio.create_task(self._run_loop())
        log.info("Started health probe")

    async def stop(self) -> None:
        if not self._running:
            log.warning("Health probe is not running")
            return
        self._running = False
        if self._loop_task:
            await cancel_and_wait(self._loop_task)
            self._loop_task = None
        log.info("Stopped health probe")

    async def register_liveness(self, checker: ServiceHealthChecker) -> None:
        self._register(checker, ProbeKind.LIVENESS)

    async def register_readiness(self, checker: ServiceHealthChecker) -> None:
        self._register(checker, ProbeKind.READINESS)

    async def register_informational(self, checker: ServiceHealthChecker) -> None:
        """Register a checker whose result is surfaced in detail `/health` but
        never gates liveness or readiness. Use for observability dependencies
        (e.g. metrics backends) whose outage should not cut traffic or restart
        the process.
        """
        self._register(checker, ProbeKind.INFORMATIONAL)

    def _register(self, checker: ServiceHealthChecker, kind: ProbeKind) -> None:
        service_group = checker.target_service_group
        target = self._target_set(kind)

        if checker in target:
            raise HealthCheckerAlreadyRegistered(
                f"Health checker already registered for {service_group} on {kind.value} probe"
            )
        for existing in self._all_checkers():
            if existing.target_service_group == service_group and existing is not checker:
                raise HealthCheckerAlreadyRegistered(
                    f"A different checker instance is already registered for {service_group}"
                )
        target.add(checker)

    def _target_set(self, kind: ProbeKind) -> set[ServiceHealthChecker]:
        match kind:
            case ProbeKind.LIVENESS:
                return self._liveness
            case ProbeKind.READINESS:
                return self._readiness
            case ProbeKind.INFORMATIONAL:
                return self._informational

    def _all_checkers(self) -> set[ServiceHealthChecker]:
        return self._liveness | self._readiness | self._informational

    async def check_all(self) -> AllServicesHealth:
        """Run every registered checker once and store the latest results."""
        snapshot: list[ServiceHealthChecker] = list(self._all_checkers())
        now = datetime.now(UTC)

        tasks = [self._check_single(c.target_service_group, c, now) for c in snapshot]
        results_or_exc = await asyncio.gather(*tasks, return_exceptions=True)

        results: dict[ServiceGroup, ServiceHealth] = {}
        for checker, result_or_exc in zip(snapshot, results_or_exc, strict=True):
            service_group = checker.target_service_group
            if isinstance(result_or_exc, BaseException):
                log.error("Unexpected error checking {}: {}", service_group, result_or_exc)
                continue
            results[service_group] = result_or_exc

        self._results.update(results)
        return AllServicesHealth(results=results)

    async def _run_loop(self) -> None:
        log.debug("Health probe loop started (check interval: {}s)", self._options.check_interval)
        try:
            while self._running:
                try:
                    await self.check_all()
                except Exception as e:
                    log.error("Error in health probe loop: {}", e, exc_info=True)
                finally:
                    await asyncio.sleep(self._options.check_interval)
        except asyncio.CancelledError:
            log.debug("Health probe loop cancelled")
            raise
        finally:
            log.debug("Health probe loop stopped")

    async def _check_single(
        self,
        service_group: ServiceGroup,
        checker: ServiceHealthChecker,
        check_time: datetime,
    ) -> ServiceHealth:
        try:
            result = await asyncio.wait_for(checker.check_service(), timeout=checker.timeout)
            log.debug("Health check succeeded for {}", service_group)
            return result
        except TimeoutError:
            log.warning("Health check timed out for {} after {}s", service_group, checker.timeout)
            return ServiceHealth(results={})
        except Exception as e:
            log.error("Health check failed for {}: {}", service_group, e, exc_info=True)
            return ServiceHealth(results={})

    async def get_connectivity_status(self) -> ConnectivityCheckResponse:
        """Return connectivity status across every registered checker, including
        informational ones. Used by the detail `/health` endpoint."""
        return self._build_connectivity_response(self._service_groups(self._all_checkers()))

    async def get_liveness_status(self) -> ConnectivityCheckResponse:
        """Return connectivity status for liveness-registered checkers only.

        Informational and readiness-only checkers are excluded — only failures
        that warrant a process restart contribute to `overall_healthy`.
        """
        return self._build_connectivity_response(self._service_groups(self._liveness))

    async def get_readiness_status(self) -> ConnectivityCheckResponse:
        """Return connectivity status for readiness.

        Liveness-registered checkers are included as well — a process that is
        not alive cannot be ready. Informational checkers are excluded.
        """
        return self._build_connectivity_response(
            self._service_groups(self._liveness | self._readiness)
        )

    @staticmethod
    def _service_groups(checkers: set[ServiceHealthChecker]) -> set[ServiceGroup]:
        return {c.target_service_group for c in checkers}

    def _build_connectivity_response(
        self,
        service_groups: set[ServiceGroup],
    ) -> ConnectivityCheckResponse:
        components: list[ComponentConnectivityStatus] = []
        for service_group in service_groups:
            result = self._results.get(service_group)
            if result is None:
                continue
            for component_id, status in result.results.items():
                components.append(
                    ComponentConnectivityStatus(
                        service_group=service_group,
                        component_id=component_id,
                        is_healthy=status.is_healthy,
                        last_checked_at=status.last_checked_at,
                        error_message=status.error_message,
                    )
                )

        overall_healthy = all(c.is_healthy for c in components) if components else True
        return ConnectivityCheckResponse(
            overall_healthy=overall_healthy,
            connectivity_checks=components,
            timestamp=datetime.now(UTC),
        )
