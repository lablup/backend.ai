"""What a domain scenario table says besides the call.

How the adapter is built lives in the tables' own conftest, and the rows a scenario
lays come from ``seeds``. This holds what is left: the type a domain table is written
against, and the situations worth naming more than once.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timedelta

from bai_scenario.seeds.rbac.role import seed_permission, seed_role
from bai_scenario.seeds.resource_policy.keypair import seed_keypair_policy
from bai_scenario.seeds.resource_policy.user import seed_user_policy
from bai_scenario.seeds.seeder import Given, Seeder
from bai_scenario.seeds.user.keypair import seed_default_keypair
from bai_scenario.seeds.user.user import seed_user

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
    recent,
)

type DomainScenario = TypedScenario[DomainAdapter, ManagerUnifiedConfig]

MANAGER_CONFIG = config_of(ManagerUnifiedConfig)


def seed_someone_of(
    seed: Seeder,
    domain: Given[DomainData],
    *,
    role: UserRole = UserRole.USER,
    vfolder_hosts: Sequence[str] = (),
) -> Given[UserData]:
    """A user of that domain, with the key they authorize with, granted nothing.

    The keypair is not optional scenery: a request that resolves the caller's key
    finds nothing without it, and fails before any permission is looked at.
    """
    policy = seed.creating(seed_user_policy())
    key_policy = seed.creating(seed_keypair_policy(vfolder_hosts=vfolder_hosts))
    someone = seed.creating(seed_user(role=role), domain, policy)
    seed.adding(seed_default_keypair(key_policy.describe), someone)
    return someone


def seed_someone_reading_domains(
    seed: Seeder, domain: Given[DomainData]
) -> tuple[Given[UserData], Given[None]]:
    """A user, and the grant that lets them read domains in that domain's scope.

    The two are answered apart so a row lays the grant by naming it, and the row
    beside it that wants the same user without it simply does not.
    """
    someone = seed_someone_of(seed, domain)
    role = seed.creating(seed_role(lambda d: d.id, name_hint="domain-reader"), domain)
    seed.adding(seed_permission(entity_type=DomainEntityType(), permission=Permission.READ), role)
    grant = seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
    return someone, grant


def enforcement_off(seed: Seeder) -> Situation[ManagerUnifiedConfig]:
    """What this scenario laid, in an install that does not enforce entity
    permissions."""
    return seed.situation(
        config=[MANAGER_CONFIG.set(lambda c: c.manager.rbac.enforcement_enabled, False)]
    )


def within_the_run() -> Callable[[datetime], bool]:
    """A timestamp the run itself wrote."""
    return recent(timedelta(minutes=5))
