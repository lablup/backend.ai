"""Leader election on a coordination.k8s.io Lease: one active replica, the others standby.

Same rules as client-go's leaderelection (suggestion-1122 12.1):

| rule | how |
|---|---|
| a holder renews every `renew_interval` | each Lease call has a request timeout below `renew_deadline` |
| a holder stops working | when it has not renewed for `renew_deadline`, or another holder took the Lease |
| a standby takes over | once the record it read has not changed for `lease_duration` on its own clock |
| a holder that exits | releases the Lease so that a standby takes it at once |
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable, Coroutine
from datetime import UTC, datetime
from typing import Any, Final

import aiohttp
from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

LEASE_DURATION: Final = 15
RENEW_DEADLINE: Final = 10.0
RENEW_INTERVAL: Final = 2.0

type Record = tuple[str | None, str | None, str | None, int | None]


def _now() -> datetime:
    return datetime.now(UTC)


def _fmt(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _raw_time(value: Any) -> str | None:
    if value is None:
        return None
    return _fmt(value) if isinstance(value, datetime) else str(value)


class LeaderElector:
    _api: client.CoordinationV1Api
    _namespace: str
    _name: str
    _identity: str
    _lease_duration: int
    _renew_deadline: float
    _renew_interval: float
    _request_timeout: float
    _clock: Callable[[], float]
    _sleep: Callable[[float], Awaitable[None]]
    _observed: Record | None
    _observed_at: float
    _last_renew: float | None

    def __init__(
        self,
        api: client.ApiClient,
        namespace: str,
        name: str,
        identity: str,
        *,
        lease_duration: int = LEASE_DURATION,
        renew_deadline: float = RENEW_DEADLINE,
        renew_interval: float = RENEW_INTERVAL,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._api = client.CoordinationV1Api(api)
        self._namespace = namespace
        self._name = name
        self._identity = identity
        self._lease_duration = lease_duration
        self._renew_deadline = renew_deadline
        self._renew_interval = renew_interval
        self._request_timeout = renew_deadline / 2
        self._clock = clock
        self._sleep = sleep
        self._observed = None
        self._observed_at = 0.0
        self._last_renew = None

    async def run(self, work: Callable[[], Coroutine[Any, Any, None]]) -> None:
        """Wait for the Lease, then run `work` while holding it. Losing it stops `work` and
        returns; the caller exits so that the process restarts as a standby. An exception of
        `work` propagates."""
        while not await self.try_acquire():
            await self._sleep(self._renew_interval)
        log.info("leader elected", lease=self._name, identity=self._identity)
        task = asyncio.create_task(work())
        try:
            while not task.done():
                await asyncio.wait({task}, timeout=self._renew_interval)
                if task.done():
                    break
                if await self.try_acquire():
                    continue
                if self._holder_changed() or not self._within_deadline():
                    log.info("leadership lost", lease=self._name, identity=self._identity)
                    break
        finally:
            if not task.done():
                task.cancel()
            await asyncio.wait({task})
            await self.release()
        if not task.cancelled() and (exc := task.exception()) is not None:
            raise exc

    def _within_deadline(self) -> bool:
        return (
            self._last_renew is not None
            and self._clock() - self._last_renew <= self._renew_deadline
        )

    def _holder_changed(self) -> bool:
        return self._observed is not None and self._observed[0] not in (None, "", self._identity)

    def _observe(self, record: Record) -> None:
        """Expiry is measured from when this replica saw the record change, not from the
        holder's renewTime: the clocks of two replicas may differ."""
        if record != self._observed:
            self._observed = record
            self._observed_at = self._clock()

    async def try_acquire(self) -> bool:
        """Take or renew the Lease; False when another holder's Lease is still fresh or the
        API server did not answer."""
        now = _now()
        try:
            lease = await self._api.read_namespaced_lease(
                self._name, self._namespace, _request_timeout=self._request_timeout
            )
        except ApiException as e:
            if e.status != 404:
                log.warning("lease read failed", lease=self._name, status=e.status)
                return False
            return await self._create(now)
        except (TimeoutError, aiohttp.ClientError, OSError) as e:
            log.warning("lease read failed", lease=self._name, exc_info=e)
            return False
        spec = lease.spec
        holder = spec.holder_identity
        self._observe((
            holder,
            _raw_time(spec.renew_time),
            _raw_time(spec.acquire_time),
            spec.lease_transitions,
        ))
        duration = spec.lease_duration_seconds or self._lease_duration
        expired = self._clock() - self._observed_at > duration
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
            await self._api.replace_namespaced_lease(
                self._name, self._namespace, lease, _request_timeout=self._request_timeout
            )
        except ApiException as e:
            if e.status != 409:
                log.warning("lease update failed", lease=self._name, status=e.status)
            return False
        except (TimeoutError, aiohttp.ClientError, OSError) as e:
            log.warning("lease update failed", lease=self._name, exc_info=e)
            return False
        self._renewed()
        return True

    def _renewed(self) -> None:
        self._last_renew = self._clock()
        self._observed = (self._identity, None, None, None)
        self._observed_at = self._last_renew

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
            await self._api.create_namespaced_lease(
                self._namespace, body, _request_timeout=self._request_timeout
            )
        except ApiException as e:
            if e.status != 409:
                log.warning("lease create failed", lease=self._name, status=e.status)
            return False
        except (TimeoutError, aiohttp.ClientError, OSError) as e:
            log.warning("lease create failed", lease=self._name, exc_info=e)
            return False
        self._renewed()
        return True

    async def release(self) -> None:
        """Give up the Lease if this replica still holds it; best effort."""
        if self._last_renew is None:
            return
        self._last_renew = None
        try:
            lease = await self._api.read_namespaced_lease(
                self._name, self._namespace, _request_timeout=self._request_timeout
            )
            if lease.spec.holder_identity != self._identity:
                return
            lease.spec.holder_identity = ""
            lease.spec.lease_duration_seconds = 1
            lease.spec.renew_time = _fmt(_now())
            await self._api.replace_namespaced_lease(
                self._name, self._namespace, lease, _request_timeout=self._request_timeout
            )
            log.info("leadership released", lease=self._name, identity=self._identity)
        except (ApiException, TimeoutError, aiohttp.ClientError, OSError) as e:
            log.warning("lease release failed", lease=self._name, exc_info=e)


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
