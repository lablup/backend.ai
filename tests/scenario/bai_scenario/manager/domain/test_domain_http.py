"""The same domain table over HTTP: aiohttp server + client SDK v2."""

from __future__ import annotations

from typing import Any

import pytest
from bai_kit.manager.http import http_runner
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.wiring.domain import domain_wiring
from bai_kit.manager.wiring.domain_http import domain_routes
from bai_scenario.manager.domain.scenarios import SCENARIOS

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.testutils.scenario import Runner, Scenario, scenario_id

WIRING = domain_wiring
ROUTES = domain_routes


@pytest.fixture
def run_http(
    request: pytest.FixtureRequest,
    world_template: Any,
    test_db: str,
    engine: Any,
    recorder: ActionRecorder,
    redis_container: tuple[str, HostPortPairModel],
) -> Runner:
    return http_runner(request.module, world_template, test_db, engine, recorder, redis_container)


@pytest.mark.parametrize("s", SCENARIOS, ids=scenario_id)
async def test_domain_http(s: Scenario, run_http: Runner) -> None:
    await run_http(s)
