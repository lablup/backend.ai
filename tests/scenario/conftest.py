"""Root conftest of the scenario tree.

Infrastructure addresses, the template database, and the runners. No manager import
here: ``bai_scenario`` beside it does the manager-aware work.
"""

from __future__ import annotations

import asyncio
import os
import secrets
from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any

import pytest
from bai_scenario.config import ScenarioConfigProvider, base_config_dict, make_config
from bai_scenario.db import (
    TemplateDatabase,
    clone_database,
    create_template,
    drop_database,
    engine_for,
)
from bai_scenario.monitors import ActionRecorder
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.seeds.ops import SeedOpsProvider
from bai_scenario.seeds.seeder import Seeder
from bai_scenario.validators import build_action_validators

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.scenario_steps import Configured

pytest_plugins = [
    "ai.backend.testutils.bootstrap",
]

CLONE_TIMES_ENV = "BACKEND_CLONE_TIMES_FILE"

# Where each scenario writes what it is and how it went. One line per row, appended, so
# it survives Pants running every test file in its own process and every shard in its
# own machine. ``scripts/scenario-report.py`` turns the lines into a report.
SCENARIO_LOG_ENV = "BACKEND_SCENARIO_LOG"


@pytest.fixture(scope="session")
def template(postgres_container: tuple[str, HostPortPairModel]) -> Iterator[TemplateDatabase]:
    _, addr = postgres_container
    name = f"scenario_tpl_{secrets.token_hex(6)}"
    template = asyncio.run(create_template(addr, name))
    _note_time("template_build", template.build_seconds)
    yield template
    asyncio.run(drop_database(addr, name))


@pytest.fixture
async def test_db(template: TemplateDatabase) -> AsyncIterator[str]:
    """A fresh copy of the template for this test alone."""
    name = f"scenario_{secrets.token_hex(6)}"
    seconds = await clone_database(template, name)
    _note_time("clone", seconds)
    yield name
    await drop_database(template.addr, name)


@pytest.fixture
async def engine(template: TemplateDatabase, test_db: str) -> AsyncIterator[Any]:
    engine = engine_for(template.addr, test_db)
    yield engine
    await engine.dispose()


@pytest.fixture
def recorder() -> ActionRecorder:
    return ActionRecorder()


@pytest.fixture
def config(
    request: pytest.FixtureRequest,
    template: TemplateDatabase,
    test_db: str,
) -> ManagerConfigProvider:
    """The config this test runs under: the base, plus what a scenario overrides.

    A test that seeds through fixtures rather than a scenario table overrides nothing,
    so it gets the base.
    """
    callspec = getattr(request.node, "callspec", None)
    asked = callspec.params.get("scenario") if callspec is not None else None
    overrides = dict(asked.config()) if isinstance(asked, Configured) else {}
    return ScenarioConfigProvider(
        make_config(base_config_dict(template.addr, test_db, None), overrides)
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
def fakes() -> Sequence[object]:
    """No external fake unless the component's conftest overrides this."""
    return ()


def _note_time(kind: str, seconds: float) -> None:
    path = os.environ.get(CLONE_TIMES_ENV)
    if path:
        with open(path, "a", encoding="utf8") as f:
            f.write(f"{kind}\t{seconds:.4f}\n")


@pytest.fixture
def seed() -> Seeder:
    """행을 선언하는 자리. 시나리오 표가 쓰는 것과 같은 `Seeder`다."""
    return Seeder()


@pytest.fixture
async def seeding(seed: Seeder, engine: ExtendedAsyncSAEngine) -> AsyncIterator[SeedingSession]:
    """픽스처가 자기 행을 그 자리에서 쓰는 자리.

    쓰기 세션 하나를 테스트 내내 열어 두므로, 픽스처가 몇 개로 나뉘어도 한 트랜잭션이다.
    """
    async with SeedOpsProvider(engine).write_ops() as ops:
        yield SeedingSession(seed, ops)
