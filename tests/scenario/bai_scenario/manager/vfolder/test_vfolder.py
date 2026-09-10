"""Making and listing a folder of one's own, and who may."""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import seed_someone_of
from bai_scenario.components.vfolder import (
    VFolderScenario,
    seed_domain_with_storage,
    seed_someone_making_folders,
)
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.domain.domain import seed_domain
from bai_scenario.seeds.seeder import Seeder

from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateVFolderInput,
    SearchVFoldersInput,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.typed_scenario import TypedScenario, at, call


def ungranted_user_is_refused(seed: Seeder) -> VFolderScenario:
    home = seed.creating(seed_domain(name_hint="home"))
    someone = seed_someone_of(seed, home)
    return TypedScenario.error(
        "a-user-granted-nothing-may-not-make-a-folder",
        description="아무 권한도 받지 않은 사용자가 폴더를 만들려 하면 권한 부족으로 거부된다",
        actor=someone,
        given=seed.situation(),
        when=call(VFolderAdapter.create, CreateVFolderInput(name="denied")),
        then=NotEnoughPermission,
    )


def granted_user_lists_none(seed: Seeder) -> VFolderScenario:
    home = seed.creating(seed_domain_with_storage())
    maker, _ = seed_someone_making_folders(seed, home)
    return TypedScenario.ok(
        "a-user-who-has-made-no-folder-lists-none",
        description="폴더를 하나도 만들지 않은 사용자가 자기 폴더를 조회하면, 답은 비어 있다",
        actor=maker,
        given=seed.situation(),
        when=call(VFolderAdapter.my_search, SearchVFoldersInput()),
        then=at(lambda p: p.total_count, 0),
    )


def granted_user_makes_a_folder(seed: Seeder) -> VFolderScenario:
    home = seed.creating(seed_domain_with_storage())
    maker, _ = seed_someone_making_folders(seed, home)
    return TypedScenario.ok(
        "a-user-granted-folder-create-makes-one-of-their-own",
        description=(
            "자기 스코프에서 폴더 생성 권한을 받은 사용자가 폴더를 만들면, "
            "그 폴더의 소유는 그 사용자에게 있다"
        ),
        actor=maker,
        given=seed.situation(),
        when=call(VFolderAdapter.create, CreateVFolderInput(name="work")),
        then=at(lambda p: p.vfolder.access_control.ownership_type, "user"),
    )


BUILDERS = (granted_user_makes_a_folder, ungranted_user_is_refused, granted_user_lists_none)
SCENARIOS: list[VFolderScenario] = [build(Seeder()) for build in BUILDERS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_vfolder(scenario: VFolderScenario, run: ScenarioRunner) -> None:
    await run(scenario)
