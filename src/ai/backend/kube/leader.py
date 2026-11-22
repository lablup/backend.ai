"""Leader election on a coordination.k8s.io Lease: one active replica, the others standby.

The holder renews the Lease every `renew_interval`; a standby takes it over once it has not been
renewed for `lease_duration`. Work stops as soon as a renewal fails (suggestion-1122 12.1).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from typing import Any, Final

from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

LEASE_DURATION: Final = 15
RENEW_INTERVAL: Final = 5.0


def _now() -> datetime:
    return datetime.now(UTC)


def _fmt(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _parse(raw: Any) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=UTC)
    return datetime.fromisoformat(str(raw))


class LeaderElector:
    _api: client.CoordinationV1Api
    _namespace: str
    _name: str
    _identity: str
    _lease_duration: int
    _renew_interval: float

    def __init__(
        self,
        api: client.ApiClient,
        namespace: str,
        name: str,
        identity: str,
        *,
        lease_duration: int = LEASE_DURATION,
        renew_interval: float = RENEW_INTERVAL,
    ) -> None:
        self._api = client.CoordinationV1Api(api)
        self._namespace = namespace
        self._name = name
        self._identity = identity
        self._lease_duration = lease_duration
        self._renew_interval = renew_interval

    async def run(self, work: Callable[[], Coroutine[Any, Any, None]]) -> None:
        """Wait for the Lease, then run `work` while holding it. Losing it stops `work` and
        returns; the caller exits so that the process restarts as a standby."""
        while True:
            if await self.try_acquire():
                break
            await asyncio.sleep(self._renew_interval)
        log.info("leader elected", lease=self._name, identity=self._identity)
        task = asyncio.create_task(work())
        try:
            while not task.done():
                await asyncio.sleep(self._renew_interval)
                if not await self.try_acquire():
                    log.info("leadership lost", lease=self._name, identity=self._identity)
                    task.cancel()
                    break
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def try_acquire(self) -> bool:
        """Take or renew the Lease; False when another holder's Lease is still fresh."""
        now = _now()
        try:
            lease = await self._api.read_namespaced_lease(self._name, self._namespace)
        except ApiException as e:
            if e.status != 404:
                log.warning("lease read failed", lease=self._name, status=e.status)
                return False
            return await self._create(now)
        spec = lease.spec
        holder = spec.holder_identity
        renewed = _parse(spec.renew_time) or _parse(spec.acquire_time)
        duration = spec.lease_duration_seconds or self._lease_duration
        expired = renewed is None or now - renewed > timedelta(seconds=duration)
        if holder not in (None, "", self._identity) and not expired:
            return False
        if holder != self._identity:
            spec.acquire_time = _fmt(now)
            spec.lease_transitions = (spec.lease_transitions or 0) + 1
        spec.holder_identity = self._identity
        spec.renew_time = _fmt(now)
        spec.lease_duration_seconds = self._lease_duration
        try:
            # resourceVersion in the body makes a concurrent takeover fail with a conflict.
            await self._api.replace_namespaced_lease(self._name, self._namespace, lease)
        except ApiException as e:
            if e.status != 409:
                log.warning("lease update failed", lease=self._name, status=e.status)
            return False
        return True

    async def _create(self, now: datetime) -> bool:
        body = client.V1Lease(
            metadata=client.V1ObjectMeta(name=self._name, namespace=self._namespace),
            spec=client.V1LeaseSpec(
                holder_identity=self._identity,
                lease_duration_seconds=self._lease_duration,
                acquire_time=_fmt(now),
                renew_time=_fmt(now),
                lease_transitions=0,
            ),
        )
        try:
            await self._api.create_namespaced_lease(self._namespace, body)
        except ApiException as e:
            if e.status != 409:
                log.warning("lease create failed", lease=self._name, status=e.status)
            return False
        return True


async def run_maybe_as_leader(
    api: client.ApiClient,
    lease: tuple[str, str, str] | None,
    work: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    """`lease` is (namespace, name, identity); None runs `work` without election."""
    if lease is None:
        await work()
        return
    namespace, name, identity = lease
    await LeaderElector(api, namespace, name, identity).run(work)
