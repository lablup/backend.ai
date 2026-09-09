"""What the vfolder adapter does, said as a request, an actor, and an answer.

A folder is the first thing in this tree that a plain member is entitled to. The
member's own user preset grants vfolder CRUD on their own scope, so the same request
that a domain refuses, a folder allows, and the rows below are where that shows.
"""

from __future__ import annotations

import pytest
from bai_scenario.infra.personas import MEMBER, OTHER_MEMBER
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.seeding import USER_PRESET, holds, on_their_own_scope

from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateVFolderInput,
    SearchVFoldersInput,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.typed_scenario import (
    TypedScenario,
    at,
    call,
    every,
)

type VFolderScenario = TypedScenario[VFolderAdapter, ManagerUnifiedConfig]

# What a plain user is given when an operator sets them up: CRUD over their own
# folders, sessions and keys. Every row below that expects a folder to be made says so.
THEIR_OWN_USER_ROLE = holds(USER_PRESET, on_their_own_scope())

SCENARIOS: list[VFolderScenario] = [
    TypedScenario.error(
        # The other half of the pair below: the same request, the same actor, and no
        # grant. What changes the answer is the role, and the table says which.
        "a-member-granted-nothing-may-not-create-a-folder",
        actor=MEMBER,
        when=call(VFolderAdapter.create, CreateVFolderInput(name="ungranted")),
        then=NotEnoughPermission,
    ),
    TypedScenario.ok(
        "a-member-granted-their-own-user-role-creates-a-folder",
        actor=MEMBER,
        holding=[THEIR_OWN_USER_ROLE],
        when=call(VFolderAdapter.create, CreateVFolderInput(name="mine")),
        then=at(lambda p: p.vfolder.metadata.name, "mine"),
    ),
    TypedScenario.ok(
        "the-new-folder-belongs-to-the-member-who-asked",
        actor=MEMBER,
        holding=[THEIR_OWN_USER_ROLE],
        when=call(VFolderAdapter.create, CreateVFolderInput(name="owned")),
        then=at(lambda p: p.vfolder.access_control.ownership_type, "user"),
    ),
    TypedScenario.ok(
        "the-folder-lands-on-the-configured-host",
        actor=MEMBER,
        holding=[THEIR_OWN_USER_ROLE],
        when=call(VFolderAdapter.create, CreateVFolderInput(name="hosted")),
        then=at(lambda p: p.vfolder.host, "local:volume1"),
    ),
    TypedScenario.ok(
        "a-second-member-may-take-the-same-folder-name",
        actor=OTHER_MEMBER,
        holding=[THEIR_OWN_USER_ROLE],
        when=call(VFolderAdapter.create, CreateVFolderInput(name="mine")),
        then=at(lambda p: p.vfolder.metadata.name, "mine"),
    ),
    TypedScenario.ok(
        "a-member-who-has-made-nothing-lists-nothing",
        actor=MEMBER,
        holding=[THEIR_OWN_USER_ROLE],
        when=call(VFolderAdapter.my_search, SearchVFoldersInput()),
        then=at(lambda p: p.total_count, 0),
    ),
    TypedScenario.ok(
        "every-folder-a-member-lists-is-on-the-configured-host",
        actor=MEMBER,
        holding=[THEIR_OWN_USER_ROLE],
        when=call(VFolderAdapter.my_search, SearchVFoldersInput()),
        then=every(lambda p: p.items, at(lambda node: node.host, "local:volume1")),
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_vfolder(scenario: VFolderScenario, run: ScenarioRunner) -> None:
    await run(scenario)
