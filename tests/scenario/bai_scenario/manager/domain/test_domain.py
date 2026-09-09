"""Domain behaviour through the transport-agnostic adapter."""

from __future__ import annotations

from typing import Any

import pytest
from bai_kit.manager.config import base_config_dict
from bai_kit.manager.db import TemplateDatabase
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.typed_runner import TypedRunner
from bai_kit.manager.wiring.domain import domain_wiring
from bai_scenario.manager.domain.scenarios import SCENARIOS, DomainScenario


@pytest.fixture
def run(
    world_template: TemplateDatabase,
    test_db: str,
    engine: Any,
    recorder: ActionRecorder,
) -> TypedRunner:
    return TypedRunner(
        wiring=domain_wiring,
        engine=engine,
        world=world_template.world,
        base_config=base_config_dict(world_template.addr, test_db, None),
        recorder=recorder,
    )


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
async def test_domain(scenario: DomainScenario, run: TypedRunner) -> None:
    await run(scenario)
