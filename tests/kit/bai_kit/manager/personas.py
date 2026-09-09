"""The four fixed actors every scenario picks from. Each names a user the World seeds."""

from __future__ import annotations

from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.data.domain.types import UserInfo
from ai.backend.testutils.scenario import Persona
from bai_kit.manager.world import World

SUPERADMIN = Persona("superadmin")
DOMAIN_ADMIN = Persona("domain-admin")
MEMBER = Persona("member")
OTHER_MEMBER = Persona("other-member")

ALL_PERSONAS = (SUPERADMIN, DOMAIN_ADMIN, MEMBER, OTHER_MEMBER)


def user_data(world: World, persona: Persona) -> UserData:
    """What ``with_user`` needs: the request-context view of the persona's user."""
    seeded = world.users[persona]
    return UserData(
        user_id=seeded.id,
        is_authorized=True,
        is_admin=seeded.role in (UserRole.SUPERADMIN, UserRole.ADMIN),
        is_superadmin=seeded.role == UserRole.SUPERADMIN,
        role=seeded.role,
        domain_name=seeded.domain_name,
        domain_id=seeded.domain_id,
    )


def user_info(world: World, persona: Persona) -> UserInfo:
    """What the domain adapter's create/update take beside the DTO."""
    seeded = world.users[persona]
    return UserInfo(id=seeded.id, role=seeded.role, domain_name=seeded.domain_name)
