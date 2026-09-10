"""Creating a user, and what comes with one."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.seeder import Seeder

from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.testutils.typed_scenario import TypedScenario

type UserScenario = TypedScenario[UserAdapter, ManagerUnifiedConfig]


# Creating a user is not covered. It asks for the keypair policy marked as the default,
# and no write spec sets that flag: the column is on the row and on no creator or
# updater. Until one carries it a scenario cannot lay the policy the create looks for.

BUILDERS: tuple[Callable[[Seeder], UserScenario], ...] = ()
SCENARIOS: list[UserScenario] = [build(Seeder()) for build in BUILDERS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_user(scenario: UserScenario, run: ScenarioRunner) -> None:
    await run(scenario)
