"""Root conftest of the scenario tree.

Infrastructure addresses, the template database, and the runners. No manager import
here: the kit (``bai_kit.manager``, source root ``tests/kit``) does the manager-aware work.
"""

from __future__ import annotations

import asyncio
import os
import secrets
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from bai_kit.manager.config import base_config_dict
from bai_kit.manager.db import (
    TemplateDatabase,
    clone_database,
    create_template,
    drop_database,
    engine_for,
)
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.runner import AdapterRunner

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.testutils.scenario import Runner

pytest_plugins = [
    "ai.backend.testutils.bootstrap",
]

CLONE_TIMES_ENV = "BACKEND_CLONE_TIMES_FILE"


@pytest.fixture(scope="session")
def world_template(postgres_container: tuple[str, HostPortPairModel]) -> Iterator[TemplateDatabase]:
    _, addr = postgres_container
    name = f"scenario_tpl_{secrets.token_hex(6)}"
    template = asyncio.run(create_template(addr, name))
    _note_time("template_build", template.build_seconds)
    yield template
    asyncio.run(drop_database(addr, name))


@pytest.fixture
async def test_db(world_template: TemplateDatabase) -> AsyncIterator[str]:
    """A fresh copy of the template for this test alone."""
    name = f"scenario_{secrets.token_hex(6)}"
    seconds = await clone_database(world_template, name)
    _note_time("clone", seconds)
    yield name
    await drop_database(world_template.addr, name)


@pytest.fixture
async def engine(world_template: TemplateDatabase, test_db: str) -> AsyncIterator[Any]:
    engine = engine_for(world_template.addr, test_db)
    yield engine
    await engine.dispose()


@pytest.fixture
def recorder() -> ActionRecorder:
    return ActionRecorder()


@pytest.fixture
def run(
    request: pytest.FixtureRequest,
    world_template: TemplateDatabase,
    test_db: str,
    engine: Any,
    recorder: ActionRecorder,
) -> Runner:
    """The adapter runner for the test module's ``WIRING``."""
    return AdapterRunner(
        wiring=request.module.WIRING,
        engine=engine,
        world=world_template.world,
        base_config=base_config_dict(world_template.addr, test_db, None),
        recorder=recorder,
    )


def _note_time(kind: str, seconds: float) -> None:
    path = os.environ.get(CLONE_TIMES_ENV)
    if path:
        with open(path, "a", encoding="utf8") as f:
            f.write(f"{kind}\t{seconds:.4f}\n")
