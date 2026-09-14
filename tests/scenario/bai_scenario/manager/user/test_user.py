"""사용자 만들기, 그리고 함께 딸려 오는 것.

아직 시나리오가 없다. 사용자 생성은 기본으로 표시된 키페어 정책을 찾는데, 그 표시를 세우는
write spec이 없다. 컬럼은 행에 있지만 어느 creator에도 updater에도 없다. 그것이 생기기
전까지는 생성이 찾는 정책을 시나리오가 심을 수 없다. 후속 이슈는 BA-7814다.
"""

from __future__ import annotations

from typing import Any

import pytest
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Scenario

type UserStep = Scenario[SeedingSession, Any, UserAdapter, Any]

SCENARIOS: list[UserStep] = []


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_user(
    scenario: UserStep, adapter: UserAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
