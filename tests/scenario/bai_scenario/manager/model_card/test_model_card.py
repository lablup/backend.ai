"""Searching model cards, and who may."""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import seed_someone_of
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.domain.domain import seed_domain
from bai_scenario.seeds.seeder import Seeder

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.model_card.request import SearchModelCardsInput
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.testutils.typed_scenario import TypedScenario, at, call

type ModelCardScenario = TypedScenario[ModelCardAdapter, ManagerUnifiedConfig]


def nothing_laid_means_nothing_found(seed: Seeder) -> ModelCardScenario:
    home = seed.creating(seed_domain(name_hint="home"))
    superadmin = seed_someone_of(seed, home, role=UserRole.SUPERADMIN)
    return TypedScenario.ok(
        "a-scenario-that-laid-no-model-card-finds-none",
        description=(
            "모델 카드를 하나도 심지 않은 상태에서 슈퍼관리자가 전체 조회를 하면, 답은 비어 있다"
        ),
        actor=superadmin,
        given=seed.situation(),
        when=call(ModelCardAdapter.admin_search, SearchModelCardsInput()),
        then=at(lambda p: p.total_count, 0),
    )


def ungranted_user_is_refused(seed: Seeder) -> ModelCardScenario:
    home = seed.creating(seed_domain(name_hint="home"))
    someone = seed_someone_of(seed, home)
    return TypedScenario.error(
        "a-user-who-is-not-the-superadmin-may-not-search-every-model-card",
        description=("슈퍼관리자가 아닌 사용자가 전체 모델 카드 조회를 요청하면 역할로 막힌다"),
        actor=someone,
        given=seed.situation(),
        when=call(ModelCardAdapter.admin_search, SearchModelCardsInput()),
        then=InsufficientPrivilege,
    )


BUILDERS = (nothing_laid_means_nothing_found, ungranted_user_is_refused)
SCENARIOS: list[ModelCardScenario] = [build(Seeder()) for build in BUILDERS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_model_card(scenario: ModelCardScenario, run: ScenarioRunner) -> None:
    await run(scenario)
