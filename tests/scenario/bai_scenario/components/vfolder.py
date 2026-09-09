"""What a vfolder scenario table says besides the call."""

from __future__ import annotations

from bai_scenario.components.domain import seed_someone_of
from bai_scenario.seeds.rbac.role import seed_permission, seed_role
from bai_scenario.seeds.seeder import Given, Seeder

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.typed_scenario import TypedScenario

type VFolderScenario = TypedScenario[VFolderAdapter, ManagerUnifiedConfig]


def seed_someone_making_folders(
    seed: Seeder, domain: Given[DomainData]
) -> tuple[Given[UserData], Given[None]]:
    """A user, and the grant that lets them make and read folders of their own.

    The scope is the user themselves: a personal folder is created in the maker's own
    scope, so that is where the role has to sit.
    """
    someone = seed_someone_of(seed, domain)
    role = seed.creating(seed_role(lambda u: UserID(u.id), name_hint="folder-owner"), someone)
    seed.adding(
        seed_permission(entity_type=VFolderEntityType(), permission=Permission.CREATE), role
    )
    seed.adding(seed_permission(entity_type=VFolderEntityType(), permission=Permission.READ), role)
    grant = seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
    return someone, grant
