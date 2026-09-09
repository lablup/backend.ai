"""Write specs for a user."""

from __future__ import annotations

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.user.creators import UserCreator
from bai_scenario.seeds.seeder import SpecFromTwo

PASSWORD = "scenario-password"


def seed_user(
    *,
    name_hint: str = "user",
    role: UserRole = UserRole.USER,
    is_active: bool = True,
) -> SpecFromTwo[DomainData, UserResourcePolicyData, UserData]:
    """A user of the given domain, held to the given policy.

    Both are values earlier rows answered, so nothing here names a domain or a policy
    that some other row happens to have made.
    """

    def build(name: str, domain: DomainData, policy: UserResourcePolicyData) -> UserCreator:
        return UserCreator(
            email=f"{name}@scenario.local",
            username=name,
            password=PasswordInfo(
                password=PASSWORD,
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=1000,
                salt_size=16,
            ),
            need_password_change=False,
            domain_id=domain.id,
            role=role,
            is_active=is_active,
            resource_policy=policy.name,
        )

    return SpecFromTwo(name_hint, build)
