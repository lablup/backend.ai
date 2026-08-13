from __future__ import annotations

import uuid
from typing import Any, cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.appproxy.common.errors import WorkerNotAvailable
from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    SessionConfig,
)
from ai.backend.appproxy.coordinator.models.worker import Worker, pick_worker


class FakeResult:
    _rows: list[Any]

    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def scalars(self) -> FakeResult:
        return self

    def all(self) -> list[Any]:
        return self._rows


class FakeSession:
    """Serves pick_worker's two queries in order: WorkerAppFilter, then Worker."""

    workers: list[Worker]
    _results: list[FakeResult]

    def __init__(self, workers: list[Worker]) -> None:
        self.workers = workers
        self._results = [FakeResult([]), FakeResult(workers)]

    async def execute(self, query: Any) -> FakeResult:
        return self._results.pop(0)


class TestPickWorker:
    def _make_worker(
        self,
        authority: str,
        frontend_mode: FrontendMode,
        *,
        occupied_slots: int = 0,
    ) -> Worker:
        """A worker with 300 port slots (PORT mode) or unlimited slots (WILDCARD_DOMAIN mode)."""
        worker = Worker.create(
            uuid.uuid4(),
            authority,
            frontend_mode,
            ProxyProtocol.HTTP,
            "127.0.0.1",
            False,
            False,
            10200,
            [AppMode.INTERACTIVE],
            port_range=(10300, 10599),
            wildcard_domain=".example.com",
        )
        worker.occupied_slots = occupied_slots
        return worker

    @pytest.fixture
    def session_config(self) -> SessionConfig:
        return SessionConfig(
            id=None,
            user_uuid=uuid.uuid4(),
            project_id=uuid.uuid4(),
            access_key=None,
            domain_name="default",
        )

    @pytest.fixture(autouse=True)
    def worker_get_from_fake_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_get(session: FakeSession, worker_id: uuid.UUID, **kwargs: Any) -> Worker:
            for worker in session.workers:
                if worker.id == worker_id:
                    return worker
            raise AssertionError(f"worker {worker_id} not in fake session")

        monkeypatch.setattr(Worker, "get", fake_get)

    async def test_picks_port_worker_with_most_remaining_slots(
        self, session_config: SessionConfig
    ) -> None:
        workers = [
            self._make_worker("worker-a", FrontendMode.PORT, occupied_slots=290),
            self._make_worker("worker-b", FrontendMode.PORT, occupied_slots=45),
            self._make_worker("worker-c", FrontendMode.PORT, occupied_slots=50),
        ]
        session = cast(AsyncSession, FakeSession(workers))

        picked = await pick_worker(
            session,
            session_config,
            None,
            ProxyProtocol.HTTP,
            AppMode.INTERACTIVE,
        )

        assert picked.authority == "worker-b"

    async def test_picks_least_occupied_wildcard_worker(
        self, session_config: SessionConfig
    ) -> None:
        workers = [
            self._make_worker("wildcard-busy", FrontendMode.WILDCARD_DOMAIN, occupied_slots=500),
            self._make_worker("wildcard-idle", FrontendMode.WILDCARD_DOMAIN, occupied_slots=3),
        ]
        session = cast(AsyncSession, FakeSession(workers))

        picked = await pick_worker(
            session,
            session_config,
            None,
            ProxyProtocol.HTTP,
            AppMode.INTERACTIVE,
        )

        assert picked.authority == "wildcard-idle"

    async def test_prefers_wildcard_over_port_worker(self, session_config: SessionConfig) -> None:
        workers = [
            self._make_worker("port-idle", FrontendMode.PORT, occupied_slots=0),
            self._make_worker("wildcard-busy", FrontendMode.WILDCARD_DOMAIN, occupied_slots=999),
        ]
        session = cast(AsyncSession, FakeSession(workers))

        picked = await pick_worker(
            session,
            session_config,
            None,
            ProxyProtocol.HTTP,
            AppMode.INTERACTIVE,
        )

        assert picked.authority == "wildcard-busy"

    async def test_excludes_full_port_worker(self, session_config: SessionConfig) -> None:
        workers = [
            self._make_worker("worker-full", FrontendMode.PORT, occupied_slots=300),
            self._make_worker("worker-almost-full", FrontendMode.PORT, occupied_slots=299),
        ]
        session = cast(AsyncSession, FakeSession(workers))

        picked = await pick_worker(
            session,
            session_config,
            None,
            ProxyProtocol.HTTP,
            AppMode.INTERACTIVE,
        )

        assert picked.authority == "worker-almost-full"

    async def test_raises_when_no_worker_has_capacity(self, session_config: SessionConfig) -> None:
        # Port range is 10300-10599, so 300 slots total. All workers are full.
        workers = [
            self._make_worker("worker-full", FrontendMode.PORT, occupied_slots=300),
        ]
        session = cast(AsyncSession, FakeSession(workers))

        with pytest.raises(WorkerNotAvailable):
            await pick_worker(
                session,
                session_config,
                None,
                ProxyProtocol.HTTP,
                AppMode.INTERACTIVE,
            )
