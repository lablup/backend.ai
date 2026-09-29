from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from typing import Any

import pytest

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.ops_contract import BASE_TABLES, Actors, OpsHarness, seed_actors


@pytest.fixture
async def ops_db(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(global_entity_ids, BASE_TABLES):
        yield global_entity_ids


@pytest.fixture
async def actors(ops_db: ExtendedAsyncSAEngine) -> Actors:
    return await seed_actors(ops_db)


@pytest.fixture
def harness(ops_db: ExtendedAsyncSAEngine) -> OpsHarness:
    return OpsHarness(ops_db)


@pytest.fixture
def silent_reads_harness(ops_db: ExtendedAsyncSAEngine) -> OpsHarness:
    """A harness whose configuration records no successful read."""
    return OpsHarness(ops_db, record_reads=False)


type CallCounter = Callable[[str], list[Any]]


@pytest.fixture
def repository_calls(monkeypatch: pytest.MonkeyPatch) -> CallCounter:
    """Record every call a named ``OpsRepository`` method receives, still running it."""

    def watch(name: str) -> list[Any]:
        calls: list[Any] = []
        original = getattr(OpsRepository, name)

        async def recorded(self: OpsRepository[Any], *args: Any, **kwargs: Any) -> Any:
            calls.append(args)
            return await original(self, *args, **kwargs)

        monkeypatch.setattr(OpsRepository, name, recorded)
        return calls

    return watch
