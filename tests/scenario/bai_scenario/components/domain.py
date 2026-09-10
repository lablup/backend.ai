"""What a domain scenario table says besides the call.

How the adapter is built lives in the tables' own conftest, and the rows a scenario
lays come from ``seeds``. This holds what is left: the type a domain table is written
against, and the situations worth naming more than once.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.typed_scenario import (
    Situation,
    TypedScenario,
    config_of,
)
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_policy.keypair import SeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import SeedUserPolicy
from bai_scenario.seeds.seeder import Given, Seeder, SeedNest
from bai_scenario.seeds.user.user import SeedUserOf

type DomainScenario = TypedScenario[DomainAdapter, ManagerUnifiedConfig]

MANAGER_CONFIG = config_of(ManagerUnifiedConfig)


@dataclass(frozen=True)
class GrantedUser:
    """A user and the grant they hold, answered apart.

    The row beside it that wants the same user without the grant simply does not ask
    for one, so the two never travel as an inseparable pair.
    """

    user: Given[UserData]
    grant: Given[None]


@dataclass(frozen=True)
class SomeoneOf(SeedNest[Given[UserData]]):
    """그 도메인에 속한 사용자 한 명. 매니저가 사용자를 만드는 경로를 그대로 탄다.

    그 경로가 인증에 쓰는 키와, 자기 폴더가 사는 개인 프로젝트까지 함께 만든다. 둘 다
    장식이 아니다. 호출자를 찾는 요청이나 자기 폴더를 만드는 요청은 그 둘이 없으면 권한을
    보기도 전에 실패한다.
    """

    domain: Given[DomainData]
    role: UserRole = UserRole.USER
    vfolder_hosts: Sequence[str] = ()

    @override
    def kind(self) -> str:
        return "도메인에 속한 사용자 한 명 준비"

    @override
    def lay(self, seed: Seeder) -> Given[UserData]:
        seed.once(SeedProjectPolicy())
        policy = seed.creating(SeedUserPolicy())
        key_policy = seed.creating(SeedKeypairPolicy(vfolder_hosts=self.vfolder_hosts))
        return seed.provisioning(SeedUserOf(role=self.role), self.domain, policy, key_policy)


@dataclass(frozen=True)
class SomeoneReadingDomains(SeedNest[GrantedUser]):
    """그 도메인 범위에서 도메인을 읽을 수 있는 사용자."""

    domain: Given[DomainData]

    @override
    def kind(self) -> str:
        return "도메인 조회 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> GrantedUser:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(SeedRole(lambda d: d.id, name_hint="domain-reader"), self.domain)
        seed.adding(
            SeedPermission(entity_type=DomainEntityType(), permission=Permission.READ), role
        )
        grant = seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return GrantedUser(someone, grant)


def enforcement_off(seed: Seeder) -> Situation[ManagerUnifiedConfig]:
    """What this scenario laid, in an install that does not enforce entity
    permissions."""
    return seed.situation(
        config=[MANAGER_CONFIG.set(lambda c: c.manager.rbac.enforcement_enabled, False)]
    )
