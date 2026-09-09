"""What the session adapter answers for a read, and who may ask.

Only the read half. What a session write needs is written down in this directory's
conftest, which names the ten dependencies a read never reaches.
"""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import seed_someone_of
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.domain.domain import seed_domain
from bai_scenario.seeds.seeder import Seeder

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.typed_scenario import TypedScenario, at, call

type SessionScenario = TypedScenario[SessionAdapter, ManagerUnifiedConfig]


def nothing_laid_means_nothing_found(seed: Seeder) -> SessionScenario:
    home = seed.creating(seed_domain(name_hint="home"))
    superadmin = seed_someone_of(seed, home, role=UserRole.SUPERADMIN)
    return TypedScenario.ok(
        "a-scenario-that-laid-no-session-finds-none",
        description="세션을 하나도 심지 않은 상태에서 슈퍼관리자가 조회하면, 답은 비어 있다",
        actor=superadmin,
        given=seed.situation(),
        when=call(SessionAdapter.admin_search, AdminSearchSessionsInput()),
        then=at(lambda p: p.total_count, 0),
    )


def ungranted_user_is_refused(seed: Seeder) -> SessionScenario:
    home = seed.creating(seed_domain(name_hint="home"))
    someone = seed_someone_of(seed, home)
    return TypedScenario.error(
        "a-user-granted-nothing-may-not-search-sessions",
        description=(
            "세션 조회는 역할이 아니라 스코프 권한이 지키므로, "
            "아무 권한도 받지 않은 사용자는 권한 부족으로 거부된다"
        ),
        actor=someone,
        given=seed.situation(),
        when=call(SessionAdapter.admin_search, AdminSearchSessionsInput()),
        then=NotEnoughPermission,
    )


BUILDERS = (nothing_laid_means_nothing_found, ungranted_user_is_refused)
SCENARIOS: list[SessionScenario] = [build(Seeder()) for build in BUILDERS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_session(scenario: SessionScenario, run: ScenarioRunner) -> None:
    await run(scenario)
