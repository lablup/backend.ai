"""Making a resource group, and reading one back."""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import SomeoneOf
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.resource_group.resource_group import SeedResourceGroup
from bai_scenario.seeds.seeder import Seeder, after

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.request import CreateResourceGroupInput
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.testutils.typed_scenario import TypedScenario, at, call

type ResourceGroupScenario = TypedScenario[ResourceGroupAdapter, ManagerUnifiedConfig]


def superadmin_makes_a_resource_group(seed: Seeder) -> ResourceGroupScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    superadmin = seed.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
    return TypedScenario.ok(
        "the-superadmin-makes-a-resource-group-in-a-domain",
        description=(
            "슈퍼관리자가 도메인 아래에 리소스 그룹을 만들면, 그 이름의 그룹이 답으로 온다"
        ),
        actor=superadmin,
        given=seed.situation(),
        when=after(
            home,
            lambda d: call(
                ResourceGroupAdapter.create,
                CreateResourceGroupInput(name="compute", domain_name=d.name),
            ),
        ),
        then=at(lambda p: p.resource_group.name, "compute"),
    )


def a_seeded_group_is_read_back(seed: Seeder) -> ResourceGroupScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    group = seed.creating(SeedResourceGroup(name_hint="compute"))
    superadmin = seed.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
    return TypedScenario.ok(
        "a-resource-group-already-there-is-read-back-by-name",
        description=("리소스 그룹이 이미 있을 때 이름으로 조회하면, 그 그룹이 답으로 온다"),
        actor=superadmin,
        given=seed.situation(),
        when=after(group, lambda g: call(ResourceGroupAdapter.get, g.name)),
        then=at(lambda node: node.name, group.name),
    )


def ungranted_user_is_refused(seed: Seeder) -> ResourceGroupScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    someone = seed.within(SomeoneOf(home))
    return TypedScenario.error(
        "a-user-who-is-not-the-superadmin-may-not-make-a-resource-group",
        description=(
            "리소스 그룹 생성은 도메인 생성과 같이 전역 역할이 지키므로, "
            "슈퍼관리자가 아닌 사용자는 권한을 얼마나 받았는지와 무관하게 막힌다"
        ),
        actor=someone,
        given=seed.situation(),
        when=after(
            home,
            lambda d: call(
                ResourceGroupAdapter.create,
                CreateResourceGroupInput(name="refused", domain_name=d.name),
            ),
        ),
        then=InsufficientPrivilege,
    )


BUILDERS = (
    superadmin_makes_a_resource_group,
    a_seeded_group_is_read_back,
    ungranted_user_is_refused,
)
SCENARIOS: list[ResourceGroupScenario] = [build(Seeder()) for build in BUILDERS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_resource_group(scenario: ResourceGroupScenario, run: ScenarioRunner) -> None:
    await run(scenario)
