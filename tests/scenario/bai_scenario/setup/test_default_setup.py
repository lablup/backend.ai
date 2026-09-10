"""What the shared setups hand a scenario.

The tables lean on these every row: a user of a domain, the policies that user needs,
the role a granted actor holds. Nothing in a table says whether they are right, because
a table is about the call it makes. These say it.

They seed through the same `Seeder` the tables use, one row per fixture.
"""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import SomeoneOf
from bai_scenario.components.vfolder import STORAGE_HOST, SomeoneMakingFolders
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.seeder import Laid

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.domain.types import DomainData


@pytest.fixture
async def home(seeding: SeedingSession) -> Laid[DomainData]:
    return await seeding.creating(SeedDomain(name_hint="home", vfolder_hosts=[STORAGE_HOST]))


async def test_a_user_is_made_in_the_domain_they_were_asked_for(
    seeding: SeedingSession, home: Laid[DomainData]
) -> None:
    someone = await seeding.within(SomeoneOf(home))

    assert seeding.made(someone).domain_name == seeding.made(home).name


async def test_the_role_asked_for_is_the_role_the_user_holds(
    seeding: SeedingSession, home: Laid[DomainData]
) -> None:
    superadmin = await seeding.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
    plain = await seeding.within(SomeoneOf(home))

    assert seeding.made(superadmin).role == UserRole.SUPERADMIN
    assert seeding.made(plain).role == UserRole.USER


async def test_two_users_of_one_domain_share_the_policy_the_manager_names(
    seeding: SeedingSession, home: Laid[DomainData]
) -> None:
    """The personal project's policy has a name the manager fixes, so a second user
    must reuse the row rather than write it again."""
    first = await seeding.within(SomeoneOf(home))
    second = await seeding.within(SomeoneOf(home))

    assert seeding.made(first).id != seeding.made(second).id


async def test_a_granted_user_and_a_plain_one_can_stand_side_by_side(
    seeding: SeedingSession, home: Laid[DomainData]
) -> None:
    """A permission row and its ungranted twin are laid in the same situation, which is
    how every permission row of the tables is written."""
    granted = await seeding.within(SomeoneMakingFolders(home))
    plain = await seeding.within(SomeoneOf(home))

    assert seeding.made(granted.user).id != seeding.made(plain).id
    assert seeding.made(granted.grant) is None
