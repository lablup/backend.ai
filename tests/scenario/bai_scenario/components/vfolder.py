"""What a vfolder scenario table says besides the call."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.testutils.typed_scenario import (
    TypedScenario,
)
from bai_scenario.components.domain import GrantedUser, SomeoneOf
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest, SeedRow

type VFolderScenario = TypedScenario[VFolderAdapter, ManagerUnifiedConfig]

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
