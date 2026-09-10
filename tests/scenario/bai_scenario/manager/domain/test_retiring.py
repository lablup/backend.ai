"""Retiring, restoring and purging a domain."""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import DomainScenario, SomeoneOf
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.seeder import Seeder, after

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.request import (
    DeleteDomainInput,
    PurgeDomainInput,
    RestoreDomainInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DeleteDomainPayload,
    PurgeDomainPayload,
    RestoreDomainPayload,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.typed_scenario import (
    Exactly,
    TypedScenario,
    call,
)


def superadmin_retires_a_domain(seed: Seeder) -> DomainScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    target = seed.creating(SeedDomain(name_hint="to-delete"))
    superadmin = seed.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
    return TypedScenario.ok(
        "the-superadmin-retires-a-domain",
        description="슈퍼관리자가 도메인을 물리면, 물렸다는 답이 온다",
        actor=superadmin,
        given=seed.situation(),
        when=after(
            target, lambda d: call(DomainAdapter.admin_delete, DeleteDomainInput(name=d.name))
        ),
        then=Exactly(DeleteDomainPayload(deleted=True)),
    )


def superadmin_restores_a_domain(seed: Seeder) -> DomainScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    target = seed.creating(SeedDomain(name_hint="to-restore"))
    superadmin = seed.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
    return TypedScenario.ok(
        "restoring-answers-that-it-restored",
        description="물렸던 도메인을 되살리면, 되살렸다는 답이 온다",
        actor=superadmin,
        given=seed.situation(),
        when=after(
            target, lambda d: call(DomainAdapter.admin_restore, RestoreDomainInput(name=d.name))
        ),
        then=Exactly(RestoreDomainPayload(restored=True)),
    )


def superadmin_purges_a_domain(seed: Seeder) -> DomainScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    target = seed.creating(SeedDomain(name_hint="to-purge"))
    superadmin = seed.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
    return TypedScenario.ok(
        "purging-a-domain-nothing-else-refers-to-succeeds",
        description="아무것도 딸려 있지 않은 도메인은 완전히 지울 수 있다",
        actor=superadmin,
        given=seed.situation(),
        when=after(
            target, lambda d: call(DomainAdapter.admin_purge, PurgeDomainInput(name=d.name))
        ),
        then=Exactly(PurgeDomainPayload(purged=True)),
    )


def unknown_name_is_not_found(seed: Seeder) -> DomainScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    superadmin = seed.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
    return TypedScenario.error(
        "retiring-a-name-nothing-answers-to-is-not-found",
        description="아무 도메인도 갖지 않은 이름을 물리려 하면 대상이 없다는 것으로 거부된다",
        actor=superadmin,
        given=seed.situation(),
        when=call(DomainAdapter.admin_delete, DeleteDomainInput(name="no-such-domain")),
        then=EntityNotFoundError,
    )


def ungranted_user_is_refused(seed: Seeder) -> DomainScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    target = seed.creating(SeedDomain(name_hint="untouchable"))
    someone = seed.within(SomeoneOf(home))
    return TypedScenario.error(
        "a-user-granted-nothing-may-not-retire-a-domain",
        description="아무 권한도 받지 않은 사용자는 도메인을 물릴 수 없다",
        actor=someone,
        given=seed.situation(),
        when=after(
            target, lambda d: call(DomainAdapter.admin_delete, DeleteDomainInput(name=d.name))
        ),
        then=NotEnoughPermission,
    )


BUILDERS = (
    superadmin_retires_a_domain,
    superadmin_restores_a_domain,
    superadmin_purges_a_domain,
    unknown_name_is_not_found,
    ungranted_user_is_refused,
)
SCENARIOS: list[DomainScenario] = [build(Seeder()) for build in BUILDERS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_retiring(scenario: DomainScenario, run: ScenarioRunner) -> None:
    await run(scenario)
