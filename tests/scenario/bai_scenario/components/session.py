"""What a session scenario table says besides the call."""

from __future__ import annotations

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.typed_scenario import TypedScenario
from bai_scenario.components.domain import seed_someone_of
from bai_scenario.seeds.rbac.role import seed_permission, seed_role
from bai_scenario.seeds.seeder import Given, Seeder

type SessionScenario = TypedScenario[SessionAdapter, ManagerUnifiedConfig]


def seed_someone_making_sessions(
    seed: Seeder, domain: Given[DomainData], project: Given[ProjectData]
) -> tuple[Given[UserData], Given[None]]:
    """A user on that project's roster, allowed to make and read sessions there.

    A session names the project it belongs to, so the role sits in the project's scope
    and the grant that gives it also puts the user on the roster.
    """
    someone = seed_someone_of(seed, domain)
    role = seed.creating(seed_role(lambda p: ProjectID(p.id), name_hint="session-owner"), project)
    seed.adding(
        seed_permission(entity_type=SessionEntityType(), permission=Permission.CREATE), role
    )
    seed.adding(seed_permission(entity_type=SessionEntityType(), permission=Permission.READ), role)
    grant = seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
    return someone, grant
