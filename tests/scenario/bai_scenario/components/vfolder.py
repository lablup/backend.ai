"""What a vfolder scenario table says besides the call."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import Given
from bai_scenario.components.domain import WAS_HERE, GrantedUser, SomeoneOf
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest, SeedRow

STORAGE_HOST = "local:volume1"
"""The one host the faked storage manager answers for."""


def seed_domain_with_storage() -> SeedRow[DomainData]:
    """A domain whose folders may land on the host the fake answers for."""
    return SeedDomain(name_hint="home", vfolder_hosts=[STORAGE_HOST])


@dataclass(frozen=True)
class SomeoneMakingFolders(SeedNest[GrantedUser]):
    """자기 폴더를 만들고 조회할 수 있는 사용자.

    범위는 사용자 자신이다. 개인 폴더는 만든 사람의 스코프에 생기므로 역할도 거기 앉는다.
    """

    domain: Laid[DomainData]

    @override
    def kind(self) -> str:
        return "폴더를 만들 수 있는 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> GrantedUser:
        someone = seed.within(SomeoneOf(self.domain, vfolder_hosts=[STORAGE_HOST]))
        role = seed.creating_from(
            SeedRole(lambda u: UserID(u.id), name_hint="folder-owner"), someone
        )
        seed.adding(
            SeedPermission(entity_type=VFolderEntityType(), permission=Permission.CREATE), role
        )
        seed.adding(
            SeedPermission(entity_type=VFolderEntityType(), permission=Permission.READ), role
        )
        grant = seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return GrantedUser(someone, grant)


@dataclass(frozen=True)
class AFolderMakerAndTheirDomain:
    """폴더를 만들 수 있는 사람과, 그 폴더가 놓일 도메인."""

    domain: DomainData
    caller: UserData


@dataclass(frozen=True)
class SomeoneWhoMayMakeFolders(Given[Any, AFolderMakerAndTheirDomain]):
    """폴더 생성·조회 권한을 받은 사용자와, 그 폴더를 받아줄 도메인."""

    @override
    def describe(self) -> str:
        return "폴더를 놓을 수 있는 도메인과, 거기서 폴더를 만들 수 있는 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> AFolderMakerAndTheirDomain:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        granted = await seeding.within(SomeoneMakingFolders(domain))
        return AFolderMakerAndTheirDomain(seeding.made(domain), seeding.made(granted.user))


@dataclass(frozen=True)
class SomeoneWithNoGrant(Given[Any, AFolderMakerAndTheirDomain]):
    """폴더를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명."""

    @override
    def describe(self) -> str:
        return "폴더를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> AFolderMakerAndTheirDomain:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        return AFolderMakerAndTheirDomain(seeding.made(domain), seeding.made(caller))
