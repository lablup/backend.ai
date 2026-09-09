"""World placement, alternative 2: one database per module, shared by every scenario.

The same table as ``test_domain.py`` on a single clone. What breaks is the evidence:
seeds with fixed names collide across scenarios, and any count assertion sees the rows
earlier scenarios left. The ids below are the scenarios that cannot survive sharing.
"""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from bai_kit.manager.config import base_config_dict
from bai_kit.manager.db import TemplateDatabase, clone_database, drop_database, engine_for
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.runner import AdapterRunner
from bai_kit.manager.wiring.domain import domain_wiring
from bai_scenario.manager.domain.scenarios import SCENARIOS

from ai.backend.testutils.scenario import Runner, Scenario, scenario_id

WIRING = domain_wiring

# Scenario ids whose then assumes a database nobody else has written to. Seeds do not
# collide inside one module run because every scenario names its own rows; they would
# on any second run against the same database.
BREAKS_WHEN_SHARED = {
    "superadmin-sees-only-the-world-domain",  # total_count counts every earlier create
}


@pytest.fixture(scope="module")
def shared_db(world_template: TemplateDatabase) -> Iterator[str]:
    name = f"scenario_shared_{secrets.token_hex(6)}"
    asyncio.run(clone_database(world_template, name))
    yield name
    asyncio.run(drop_database(world_template.addr, name))


@pytest.fixture
async def shared_engine(world_template: TemplateDatabase, shared_db: str) -> AsyncIterator[Any]:
    engine = engine_for(world_template.addr, shared_db)
    yield engine
    await engine.dispose()


@pytest.fixture
def run_shared(world_template: TemplateDatabase, shared_db: str, shared_engine: Any) -> Runner:
    return AdapterRunner(
        wiring=WIRING,
        engine=shared_engine,
        world=world_template.world,
        base_config=base_config_dict(world_template.addr, shared_db, None),
        recorder=ActionRecorder(suite="shared"),
    )


def _mark(s: Scenario) -> Any:
    if s.id in BREAKS_WHEN_SHARED:
        return pytest.param(
            s, marks=pytest.mark.xfail(strict=True, reason="needs its own database")
        )
    return s


@pytest.mark.parametrize("s", [_mark(s) for s in SCENARIOS], ids=scenario_id)
async def test_domain_shared_world(s: Scenario, run_shared: Runner) -> None:
    await run_shared(s)
