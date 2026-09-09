"""What the vfolder adapter does, said as a request, an actor, and an answer.

A folder is the first thing in this tree that a plain member is entitled to. The
member's own user preset grants vfolder CRUD on their own scope, so the same request
that a domain refuses, a folder allows, and the rows below are where that shows.
"""

from __future__ import annotations

from typing import Any

import pytest
from bai_kit.manager.config import base_config_dict
from bai_kit.manager.db import TemplateDatabase
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.personas import MEMBER, OTHER_MEMBER
from bai_kit.manager.typed_runner import TypedRunner
from bai_kit.manager.wiring.vfolder import (
    create_vfolder,
    my_vfolders,
    vfolder_wiring,
)

from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateVFolderInput,
    SearchVFoldersInput,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.testutils.typed_scenario import TypedScenario, at, every

type VFolderScenario = TypedScenario[VFolderAdapter, ManagerUnifiedConfig]

SCENARIOS: list[VFolderScenario] = [
    TypedScenario.ok(
        "a-member-creates-a-folder-of-their-own",
        actor=MEMBER,
        when=create_vfolder(CreateVFolderInput(name="mine")),
        then=at(lambda p: p.vfolder.metadata.name, "mine"),
    ),
    TypedScenario.ok(
        "the-new-folder-belongs-to-the-member-who-asked",
        actor=MEMBER,
        when=create_vfolder(CreateVFolderInput(name="owned")),
        then=at(lambda p: p.vfolder.access_control.ownership_type, "user"),
    ),
    TypedScenario.ok(
        "the-folder-lands-on-the-configured-host",
        actor=MEMBER,
        when=create_vfolder(CreateVFolderInput(name="hosted")),
        then=at(lambda p: p.vfolder.host, "local:volume1"),
    ),
    TypedScenario.ok(
        "a-second-member-may-take-the-same-folder-name",
        actor=OTHER_MEMBER,
        when=create_vfolder(CreateVFolderInput(name="mine")),
        then=at(lambda p: p.vfolder.metadata.name, "mine"),
    ),
    TypedScenario.ok(
        "a-member-who-has-made-nothing-lists-nothing",
        actor=MEMBER,
        when=my_vfolders(SearchVFoldersInput()),
        then=at(lambda p: p.total_count, 0),
    ),
    TypedScenario.ok(
        "every-folder-a-member-lists-is-on-the-configured-host",
        actor=MEMBER,
        when=my_vfolders(SearchVFoldersInput()),
        then=every(lambda p: p.items, at(lambda node: node.host, "local:volume1")),
    ),
]


@pytest.fixture
def run(
    world_template: TemplateDatabase,
    test_db: str,
    engine: Any,
    recorder: ActionRecorder,
) -> TypedRunner:
    return TypedRunner(
        wiring=vfolder_wiring,
        engine=engine,
        world=world_template.world,
        base_config=base_config_dict(world_template.addr, test_db, None),
        recorder=recorder,
    )


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
async def test_vfolder(scenario: VFolderScenario, run: TypedRunner) -> None:
    await run(scenario)
