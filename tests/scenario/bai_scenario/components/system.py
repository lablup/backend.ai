"""What every system-concern table says besides the call.

A system entity is created in no scope, so a table lays no place for it: only the caller
and the rows the call reads. What tells callers apart is the role. The superadmin role
passes the global gate, the monitor role passes its reads, and a user holding nothing
passes only the reads that ask for authentication alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.seeder import Laid
from bai_scenario.seeds.user.user import SeedUserOf

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import Given

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
    """부를 사람 한 명."""

    caller: UserData


async def lay_a_caller(seeding: Any, role: UserRole = UserRole.USER) -> Laid[UserData]:
    """A user of the given role, in a domain of their own."""
    home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
    caller: Laid[UserData] = await seeding.within(SomeoneOf(home, role=role))
    return caller


@dataclass(frozen=True)
class SomeoneAlone(Given[Any, ACaller]):
    """사용자 한 명, 그리고 아무 행도 없음."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"{role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ACaller:
        caller = await lay_a_caller(seeding, self.role)
        return ACaller(seeding.made(caller))
