from __future__ import annotations

import asyncio
import copy
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.kube import leader as leader_module
from ai.backend.kube.leader import LeaderElector


class FakeClock:
    now: float

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeLeaseApi:
    """One Lease, with optimistic concurrency like the API server."""

    lease: client.V1Lease | None
    version: int
    failing: bool
    timeouts: list[float | None]

    def __init__(self) -> None:
        self.lease = None
        self.version = 0
        self.failing = False
        self.timeouts = []

    def put(self, holder: str, renew_time: datetime) -> None:
        self.version += 1
        self.lease = client.V1Lease(
            metadata=client.V1ObjectMeta(
                name="l", namespace="ns", resource_version=str(self.version)
            ),
            spec=client.V1LeaseSpec(
                holder_identity=holder,
                lease_duration_seconds=15,
                renew_time=renew_time,
                acquire_time=renew_time,
                lease_transitions=0,
            ),
        )

    def _check(self, kwargs: dict[str, Any]) -> None:
        self.timeouts.append(kwargs.get("_request_timeout"))
        if self.failing:
            raise TimeoutError

    async def read_namespaced_lease(self, _name: str, _ns: str, **kw: Any) -> client.V1Lease:
        self._check(kw)
        if self.lease is None:
            raise ApiException(status=404)
        return copy.deepcopy(self.lease)

    async def create_namespaced_lease(self, _ns: str, body: client.V1Lease, **kw: Any) -> None:
        self._check(kw)
        if self.lease is not None:
            raise ApiException(status=409)
        self.version += 1
        body.metadata.resource_version = str(self.version)
        self.lease = body

    async def replace_namespaced_lease(
        self, _name: str, _ns: str, body: client.V1Lease, **kw: Any
    ) -> None:
        self._check(kw)
        assert self.lease is not None
        if body.metadata.resource_version != self.lease.metadata.resource_version:
            raise ApiException(status=409)
        self.version += 1
        body.metadata.resource_version = str(self.version)
        self.lease = body


class WorkFailed(Exception):
    pass


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> FakeLeaseApi:
    fake = FakeLeaseApi()
    monkeypatch.setattr(client, "CoordinationV1Api", lambda _api: fake)
    return fake


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def _elector(identity: str, clock: FakeClock, **kw: Any) -> LeaderElector:
    return LeaderElector(client.ApiClient(), "ns", "l", identity, clock=clock, **kw)


class TestStandby:
    async def test_waits_a_lease_duration_from_its_own_observation(
        self, api: FakeLeaseApi, clock: FakeClock
    ) -> None:
        # The holder's renewTime is an hour old by our clock: a skewed clock, not a dead holder.
        api.put("other", datetime.now(UTC) - timedelta(hours=1))
        standby = _elector("me", clock)
        assert not await standby.try_acquire()
        clock.advance(14)
        assert not await standby.try_acquire()
        clock.advance(2)
        assert await standby.try_acquire()
        assert api.lease is not None and api.lease.spec.holder_identity == "me"

    async def test_a_renewing_holder_is_never_taken_over(
        self, api: FakeLeaseApi, clock: FakeClock
    ) -> None:
        api.put("other", datetime.now(UTC) + timedelta(hours=1))
        standby = _elector("me", clock)
        for _ in range(5):
            assert not await standby.try_acquire()
            clock.advance(10)
            api.put("other", datetime.now(UTC) + timedelta(hours=1, seconds=clock.now))
        assert not await standby.try_acquire()

    async def test_every_lease_call_has_a_timeout_below_the_renew_deadline(
        self, api: FakeLeaseApi, clock: FakeClock
    ) -> None:
        elector = _elector("me", clock)
        await elector.try_acquire()
        await elector.try_acquire()
        assert api.timeouts
        assert all(t is not None and t < leader_module.RENEW_DEADLINE for t in api.timeouts)


class TestLeader:
    async def test_stops_working_when_renewals_fail_past_the_deadline(
        self, api: FakeLeaseApi
    ) -> None:
        elector = LeaderElector(
            client.ApiClient(),
            "ns",
            "l",
            "me",
            lease_duration=2,
            renew_deadline=0.2,
            renew_interval=0.02,
        )
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def work() -> None:
            started.set()
            api.failing = True
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        await asyncio.wait_for(elector.run(work), timeout=5)
        assert started.is_set() and cancelled.is_set()

    async def test_stops_at_once_when_another_holder_takes_the_lease(
        self, api: FakeLeaseApi
    ) -> None:
        elector = LeaderElector(
            client.ApiClient(),
            "ns",
            "l",
            "me",
            lease_duration=60,
            renew_deadline=30,
            renew_interval=0.02,
        )

        async def work() -> None:
            api.put("other", datetime.now(UTC))
            await asyncio.sleep(60)

        await asyncio.wait_for(elector.run(work), timeout=5)
        assert api.lease is not None and api.lease.spec.holder_identity == "other"

    async def test_work_failure_propagates_and_releases_the_lease(
        self, api: FakeLeaseApi, clock: FakeClock
    ) -> None:
        async def work() -> None:
            raise WorkFailed

        with pytest.raises(WorkFailed):
            await _elector("me", clock).run(work)
        assert api.lease is not None and api.lease.spec.holder_identity == ""

    async def test_finished_work_releases_the_lease(
        self, api: FakeLeaseApi, clock: FakeClock
    ) -> None:
        async def work() -> None:
            pass

        await _elector("me", clock).run(work)
        assert api.lease is not None and api.lease.spec.holder_identity == ""
