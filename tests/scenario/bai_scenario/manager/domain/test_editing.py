"""Editing a domain, and who may."""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import DomainScenario, SomeoneOf
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.seeder import Seeder, after

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.request import UpdateDomainInput
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.typed_scenario import TypedScenario, at, call, needs_actor


def superadmin_edits_a_description(seed: Seeder) -> DomainScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    editable = seed.creating(SeedDomain(name_hint="editable"))
    superadmin = seed.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
    # ``description`` is optional on the node, so what it is held to has to be too.
    edited: str | None = "edited"
    return TypedScenario.ok(
        "editing-a-description-leaves-the-name-alone",
        description=(
            "슈퍼관리자가 도메인의 설명만 바꾸면, 설명은 새 값이 되고 이름은 그대로 남는다"
        ),
        actor=superadmin,
        given=seed.situation(),
        when=after(
            editable,
            lambda d: needs_actor(
                lambda actor: call(
                    DomainAdapter.admin_update,
                    d.name,
                    UpdateDomainInput(description="edited"),
                    actor,
                ),
                "admin_update",
            ),
        ),
        then=at(lambda p: p.domain.basic_info.description, edited),
    )


def retiring_is_an_edit_of_the_active_flag(seed: Seeder) -> DomainScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    target = seed.creating(SeedDomain(name_hint="to-retire"))
    superadmin = seed.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
    return TypedScenario.ok(
        "clearing-the-active-flag-is-how-a-domain-retires",
        description="활성 플래그를 내리는 수정으로 도메인을 물릴 수 있고, 답이 그 상태를 실어 온다",
        actor=superadmin,
        given=seed.situation(),
        when=after(
            target,
            lambda d: needs_actor(
                lambda actor: call(
                    DomainAdapter.admin_update, d.name, UpdateDomainInput(is_active=False), actor
                ),
                "admin_update",
            ),
        ),
        then=at(lambda p: p.domain.lifecycle.is_active, False),
    )


def unknown_name_is_not_found(seed: Seeder) -> DomainScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    superadmin = seed.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
    return TypedScenario.error(
        "editing-a-name-nothing-answers-to-is-not-found",
        description="아무 도메인도 갖지 않은 이름을 수정하려 하면 대상이 없다는 것으로 거부된다",
        actor=superadmin,
        given=seed.situation(),
        when=needs_actor(
            lambda actor: call(
                DomainAdapter.admin_update,
                "no-such-domain",
                UpdateDomainInput(description="x"),
                actor,
            ),
            "admin_update",
        ),
        then=EntityNotFoundError,
    )


def ungranted_user_is_refused(seed: Seeder) -> DomainScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    target = seed.creating(SeedDomain(name_hint="untouchable"))
    someone = seed.within(SomeoneOf(home))
    return TypedScenario.error(
        "a-user-granted-nothing-may-not-edit-a-domain",
        description="아무 권한도 받지 않은 사용자가 도메인을 수정하려 하면 권한 부족으로 거부된다",
        actor=someone,
        given=seed.situation(),
        when=after(
            target,
            lambda d: needs_actor(
                lambda actor: call(
                    DomainAdapter.admin_update,
                    d.name,
                    UpdateDomainInput(description="x"),
                    actor,
                ),
                "admin_update",
            ),
        ),
        then=NotEnoughPermission,
    )


BUILDERS = (
    superadmin_edits_a_description,
    retiring_is_an_edit_of_the_active_flag,
    unknown_name_is_not_found,
    ungranted_user_is_refused,
)
SCENARIOS: list[DomainScenario] = [build(Seeder()) for build in BUILDERS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_editing(scenario: DomainScenario, run: ScenarioRunner) -> None:
    await run(scenario)
