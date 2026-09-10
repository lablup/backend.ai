"""What the session adapter answers for a read, and who may ask.

Only the read half. What a session write needs is written down in this directory's
conftest, which names the ten dependencies a read never reaches.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from bai_scenario.components.domain import SomeoneOf
from bai_scenario.components.session import SessionScenario, SomeoneMakingSessions
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.image.image import SeedImage
from bai_scenario.seeds.image.registry import SeedContainerRegistry
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.resource_group.resource_group import (
    LinkToDomain,
    SeedResourceGroup,
)
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.seeder import Seeder, after_three

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.session.request import (
    AdminSearchSessionsInput,
    EnqueueSessionInput,
)
from ai.backend.common.dto.manager.v2.session.types import CreateSessionTypeEnum
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.typed_scenario import TypedScenario, at, call, needs_actor


def nothing_laid_means_nothing_found(seed: Seeder) -> SessionScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    superadmin = seed.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
    return TypedScenario.ok(
        "a-scenario-that-laid-no-session-finds-none",
        description="세션을 하나도 심지 않은 상태에서 슈퍼관리자가 조회하면, 답은 비어 있다",
        actor=superadmin,
        given=seed.situation(),
        when=call(SessionAdapter.admin_search, AdminSearchSessionsInput()),
        then=at(lambda p: p.total_count, 0),
    )


def ungranted_user_is_refused(seed: Seeder) -> SessionScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    someone = seed.within(SomeoneOf(home))
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


def granted_user_enqueues_a_session(seed: Seeder) -> SessionScenario:
    home = seed.creating(SeedDomain(name_hint="home"))
    group = seed.creating(SeedResourceGroup(name_hint="compute"))
    seed.linking(LinkToDomain(), home, group)
    registry = seed.creating(SeedContainerRegistry())
    image = seed.creating_from(SeedImage(name_hint="python"), registry)
    policy = seed.once(SeedProjectPolicy())
    project = seed.creating_from_two(SeedProject(name_hint="research"), home, policy)
    maker = seed.within(SomeoneMakingSessions(home, project)).user
    return TypedScenario.ok(
        "a-user-granted-session-create-enqueues-one",
        description=(
            "이미지와 리소스 그룹이 있고 자기 스코프에서 세션 생성 권한을 받은 사용자가 "
            "세션을 요청하면, 그 세션이 대기 상태로 등록된다"
        ),
        actor=maker,
        given=seed.situation(),
        when=after_three(
            image,
            group,
            project,
            lambda img, rg, proj: needs_actor(
                lambda actor: call(
                    SessionAdapter.enqueue,
                    EnqueueSessionInput(
                        session_name="first",
                        session_type=CreateSessionTypeEnum.INTERACTIVE,
                        image_id=img.id,
                        resource_entries=[],
                        resource_group_id=ResourceGroupID(rg.id),
                        project_id=proj.id,
                    ),
                    actor.id,
                    str(actor.role),
                    "",
                    actor.domain_name,
                    proj.id,
                ),
                "enqueue",
            ),
        ),
        then=at(lambda p: p.session.project_id, project.name and UUID(int=0)),
    )


# Enqueueing runs the whole way now: the controller is wired, the resource group is
# allowed for the domain, the image and the project are there, and the pre-enqueue hook
# dispatches to nobody. What it stops on is that the group serves no resource slot,
# which wants an agent — and an agent has no write spec at all. One registers itself by
# heartbeat, so a scenario cannot lay one the way it lays every other row.

BUILDERS = (nothing_laid_means_nothing_found, ungranted_user_is_refused)
SCENARIOS: list[SessionScenario] = [build(Seeder()) for build in BUILDERS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_session(scenario: SessionScenario, run: ScenarioRunner) -> None:
    await run(scenario)
