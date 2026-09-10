"""Making a project, and putting somebody on its roster."""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import seed_personal_project_policy, seed_someone_of
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.domain.domain import seed_domain
from bai_scenario.seeds.project.project import seed_project
from bai_scenario.seeds.rbac.role import seed_role
from bai_scenario.seeds.seeder import Seeder, after

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.group.request import (
    AssignUsersToProjectInput,
    CreateProjectInput,
)
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.typed_scenario import TypedScenario, at, call

type ProjectScenario = TypedScenario[ProjectAdapter, ManagerUnifiedConfig]


def superadmin_makes_a_project(seed: Seeder) -> ProjectScenario:
    home = seed.creating(seed_domain(name_hint="home"))
    policy = seed_personal_project_policy(seed)
    superadmin = seed_someone_of(seed, home, role=UserRole.SUPERADMIN)
    return TypedScenario.ok(
        "the-superadmin-makes-a-project-in-a-domain",
        description=(
            "도메인과 프로젝트 정책이 있을 때 슈퍼관리자가 프로젝트를 만들면, "
            "그 이름의 프로젝트가 그 도메인 아래에 생긴다"
        ),
        actor=superadmin,
        given=seed.situation(),
        when=after(
            home,
            policy,
            lambda d, pol: call(
                ProjectAdapter.admin_create,
                CreateProjectInput(name="research", domain_name=d.name, resource_policy=pol.name),
            ),
        ),
        then=at(lambda p: p.project.basic_info.name, "research"),
    )


def plain_user_may_not_make_a_project(seed: Seeder) -> ProjectScenario:
    home = seed.creating(seed_domain(name_hint="home"))
    policy = seed_personal_project_policy(seed)
    someone = seed_someone_of(seed, home)
    return TypedScenario.error(
        "a-user-granted-nothing-may-not-make-a-project",
        description=(
            "프로젝트 생성은 역할이 아니라 도메인 스코프의 권한이 지키므로, "
            "아무 권한도 받지 않은 사용자는 권한 부족으로 거부된다"
        ),
        actor=someone,
        given=seed.situation(),
        when=after(
            home,
            policy,
            lambda d, pol: call(
                ProjectAdapter.admin_create,
                CreateProjectInput(name="refused", domain_name=d.name, resource_policy=pol.name),
            ),
        ),
        then=NotEnoughPermission,
    )


def a_member_joins_a_project(seed: Seeder) -> ProjectScenario:
    home = seed.creating(seed_domain(name_hint="home"))
    policy = seed_personal_project_policy(seed)
    project = seed.creating(seed_project(name_hint="research"), home, policy)
    member = seed_someone_of(seed, home)
    role = seed.creating(seed_role(lambda p: ProjectID(p.id), name_hint="project-member"), project)
    superadmin = seed_someone_of(seed, home, role=UserRole.SUPERADMIN)
    return TypedScenario.ok(
        "assigning-a-user-to-a-project-puts-them-on-its-roster",
        description=(
            "프로젝트와 그 프로젝트 스코프의 역할이 있을 때 사용자를 배정하면, "
            "그 사용자가 명부에 오른다"
        ),
        actor=superadmin,
        given=seed.situation(),
        when=after(
            project,
            member,
            role,
            lambda p, u, r: call(
                ProjectAdapter.assign_users,
                p.id,
                AssignUsersToProjectInput(user_ids=[u.id], role_id=r.id),
            ),
        ),
        then=at(lambda p: len(p.items), 1),
    )


BUILDERS = (
    superadmin_makes_a_project,
    plain_user_may_not_make_a_project,
    a_member_joins_a_project,
)
SCENARIOS: list[ProjectScenario] = [build(Seeder()) for build in BUILDERS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_project(scenario: ProjectScenario, run: ScenarioRunner) -> None:
    await run(scenario)
