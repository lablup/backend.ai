"""What a session scenario table says besides the call."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from bai_scenario.components.domain import GrantedUser, SomeoneOf
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest


@dataclass(frozen=True)
class SomeoneMakingSessions(SeedNest[GrantedUser]):
    """그 프로젝트에서 세션을 만들고 조회할 수 있는 사용자.

    세션은 자기가 속한 프로젝트를 이름으로 대므로 역할이 프로젝트 스코프에 앉고, 그 역할을
    주는 일이 곧 그 사람을 프로젝트 명부에 올리는 일이 된다.
    """

    domain: Laid[DomainData]
    project: Laid[ProjectData]

    @override
    def kind(self) -> str:
        return "그 프로젝트에서 세션을 만들 수 있는 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> GrantedUser:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            SeedRole(lambda p: ProjectID(p.id), name_hint="session-owner"), self.project
        )
        seed.adding(
            SeedPermission(entity_type=SessionEntityType(), permission=Permission.CREATE), role
        )
        seed.adding(
            SeedPermission(entity_type=SessionEntityType(), permission=Permission.READ), role
        )
        grant = seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return GrantedUser(someone, grant)
