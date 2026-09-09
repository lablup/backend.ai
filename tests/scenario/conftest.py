"""Root conftest of the scenario tree.

Infrastructure addresses, the template database, and the runners. No manager import
here: ``bai_scenario`` beside it does the manager-aware work.
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any

import pytest
from bai_scenario.infra.config import ScenarioConfigProvider, base_config_dict, make_config
from bai_scenario.infra.db import (
    TemplateDatabase,
    clone_database,
    create_template,
    drop_database,
    engine_for,
)
from bai_scenario.infra.monitors import ActionRecorder
from bai_scenario.infra.validators import build_action_validators
from bai_scenario.runner.runner import ScenarioRunner

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

pytest_plugins = [
    "ai.backend.testutils.bootstrap",
]

CLONE_TIMES_ENV = "BACKEND_CLONE_TIMES_FILE"

# Where each scenario writes what it is and how it went. One line per row, appended, so
# it survives Pants running every test file in its own process and every shard in its
# own machine. ``scripts/scenario-report.py`` turns the lines into a report.
SCENARIO_LOG_ENV = "BACKEND_SCENARIO_LOG"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> Any:
    """Record what each scenario said about itself, beside how it went."""
    report = yield
    path = os.environ.get(SCENARIO_LOG_ENV)
    if path is None or call.when != "call":
        return report
    callspec = getattr(item, "callspec", None)
    scenario = callspec.params.get("scenario") if callspec is not None else None
    described = getattr(scenario, "describe", None)
    if described is None:
        return report
    result = report.get_result()
    module = getattr(item, "module", None)
    kit = getattr(module, "KIT", None)
    row = {
        **described(),
        "module": getattr(module, "__name__", ""),
        "outcome": result.outcome,
        "adapter": kit.adapter_type.__name__ if kit is not None else "",
        "offers": sorted(kit.operations()) if kit is not None else [],
    }
    with open(path, "a", encoding="utf8") as f:
        f.write(json.dumps(row) + "\n")
    return report


@pytest.fixture(scope="session")
def world_template(postgres_container: tuple[str, HostPortPairModel]) -> Iterator[TemplateDatabase]:
    _, addr = postgres_container
    name = f"scenario_tpl_{secrets.token_hex(6)}"
    template = asyncio.run(create_template(addr, name))
    _note_time("template_build", template.build_seconds)
    _note_time("schema", template.schema_seconds)
    _note_time("world", template.world_seconds)
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
def config(
    request: pytest.FixtureRequest,
    world_template: TemplateDatabase,
    test_db: str,
) -> ManagerConfigProvider:
    """The config this row runs under: the base, plus what the row overrides."""
    scenario = request.node.callspec.params["scenario"]
    return ScenarioConfigProvider(
        make_config(
            base_config_dict(world_template.addr, test_db, None),
            scenario.given.dotted_config(),
        )
    )


@pytest.fixture
def validators(
    engine: Any, config: ManagerConfigProvider
) -> tuple[ActionValidators, V2ActionValidators]:
    return build_action_validators(PermissionControllerRepository(engine), config)


@pytest.fixture
def monitors(recorder: ActionRecorder) -> ActionMonitors:
    return recorder.monitors()


@pytest.fixture
def run(adapter: Any, engine: Any, fakes: Sequence[object]) -> ScenarioRunner:
    """The runner for the adapter the component's own conftest built."""
    return ScenarioRunner(adapter=adapter, engine=engine, fakes=fakes)


@pytest.fixture
def fakes() -> Sequence[object]:
    """No external fake unless the component's conftest overrides this."""
    return ()


def _note_time(kind: str, seconds: float) -> None:
    path = os.environ.get(CLONE_TIMES_ENV)
    if path:
        with open(path, "a", encoding="utf8") as f:
            f.write(f"{kind}\t{seconds:.4f}\n")
