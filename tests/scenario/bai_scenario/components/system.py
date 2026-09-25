"""What every system-concern table says besides the call.

A system entity is created in no scope, so a table lays no place for it: only the caller
and the rows the call reads. What tells callers apart is the role. The superadmin role
passes the global gate, the monitor role passes its reads, and a user holding nothing
passes only the reads that ask for authentication alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import Given
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest
from bai_scenario.seeds.user.user import SeedUserOf

ENFORCEMENT = "manager.rbac.enforcement_enabled"
"""The switch the entity gate reads. A row that turns it off passes it as its config."""


class Kept:
    """A place an edit must leave as the seed laid it."""


KEPT = Kept()


def role_named(role: UserRole) -> str:
    """What the report calls a user of this role, the same way the seed does."""
    return SeedUserOf(role=role).kind()


@dataclass(frozen=True)
class ACaller:
    """호출자 한 명."""

    caller: UserData


async def lay_a_caller(seeding: Any, role: UserRole = UserRole.USER) -> Laid[UserData]:
    """A user of the given role, in a domain of their own."""
    home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
    caller: Laid[UserData] = await seeding.within(SomeoneOf(home, role=role))
    return caller


@dataclass(frozen=True)
class SomeoneReadingInPublic(SeedNest[Laid[UserData]]):
    """그 사용자에게 public 에서 한 엔티티 타입을 읽을 권한을 준다.

    설치본은 모든 계정에 public_member 를 자동으로 붙이지만 시나리오 스키마는 시드 역할을
    만들지 않는다. 그래서 같은 범위를 시나리오가 직접 역할로 준다.
    """

    domain: Laid[Any]
    entity_type: EntityType
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        return f"public 에서 {self.entity_type} 조회 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain, role=self.role))
        granted = seed.creating_from(
            SeedRole(
                lambda _: global_entity_id(GlobalEntityName.PUBLIC), name_hint="public-reader"
            ),
            someone,
        )
        seed.adding(
            SeedPermission(entity_type=self.entity_type, permission=Permission.READ), granted
        )
        seed.granting(granted, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


async def lay_a_public_reader(
    seeding: Any, entity_type: EntityType, role: UserRole = UserRole.USER
) -> Laid[UserData]:
    """A user of the given role who reads one entity type in public."""
    home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
    caller: Laid[UserData] = await seeding.within(
        SomeoneReadingInPublic(home, entity_type, role=role)
    )
    return caller


@dataclass(frozen=True)
class SomeoneAlone(Given[Any, ACaller]):
    """사용자 한 명만 있고 다른 데이터는 없다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"{role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ACaller:
        caller = await lay_a_caller(seeding, self.role)
        return ACaller(seeding.made(caller))
