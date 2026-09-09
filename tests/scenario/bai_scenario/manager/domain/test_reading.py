"""Reading one domain by name, and who is allowed to."""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import DomainScenario, seed_someone_of
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.domain.domain import seed_domain
from bai_scenario.seeds.seeder import Seeder, after

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.typed_scenario import TypedScenario, at, call


def superadmin_reads_by_name(seed: Seeder) -> DomainScenario:
    domain = seed.creating(seed_domain(name_hint="host"))
    superadmin = seed_someone_of(seed, domain, role=UserRole.SUPERADMIN)
    return TypedScenario.ok(
        "the-superadmin-reads-a-domain-by-name",
        description=("도메인 하나가 있고 슈퍼관리자가 이름으로 조회하면, 그 도메인이 답으로 온다"),
        actor=superadmin,
        given=seed.situation(),
        when=after(domain, lambda d: call(DomainAdapter.get, d.name)),
        then=at(lambda node: node.basic_info.name, domain.describe),
    )


def ungranted_user_is_refused(seed: Seeder) -> DomainScenario:
    domain = seed.creating(seed_domain(name_hint="host"))
    stranger = seed_someone_of(seed, domain)
    return TypedScenario.error(
        "a-user-granted-nothing-may-not-read-a-domain",
        description=(
            "같은 도메인이 있고 사용자가 아무 권한도 받지 않았을 때, "
            "이름으로 조회하면 권한 부족으로 거부된다"
        ),
        actor=stranger,
        given=seed.situation(),
        when=after(domain, lambda d: call(DomainAdapter.get, d.name)),
        then=NotEnoughPermission,
    )


def unknown_name_is_not_found(seed: Seeder) -> DomainScenario:
    domain = seed.creating(seed_domain(name_hint="host"))
    superadmin = seed_someone_of(seed, domain, role=UserRole.SUPERADMIN)
    return TypedScenario.error(
        "reading-a-name-nothing-answers-to-is-not-found",
        description=(
            "슈퍼관리자가 존재하지 않는 이름으로 조회하면, "
            "권한 문제가 아니라 대상이 없다는 것으로 거부된다"
        ),
        actor=superadmin,
        given=seed.situation(),
        when=call(DomainAdapter.get, "no-such-domain"),
        then=EntityNotFoundError,
    )


BUILDERS = (
    superadmin_reads_by_name,
    ungranted_user_is_refused,
    unknown_name_is_not_found,
)
SCENARIOS: list[DomainScenario] = [build(Seeder()) for build in BUILDERS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_reading(scenario: DomainScenario, run: ScenarioRunner) -> None:
    await run(scenario)
