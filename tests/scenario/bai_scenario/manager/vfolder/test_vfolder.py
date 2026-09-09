"""Making and listing a folder of one's own, and who may."""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import seed_someone_of
from bai_scenario.components.vfolder import VFolderScenario
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.domain.domain import seed_domain
from bai_scenario.seeds.seeder import Seeder

from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateVFolderInput,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.typed_scenario import TypedScenario, call


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


# The other half of this pair is missing. A role scoped to the maker's own scope, with
# vfolder CREATE on it, does not let the maker create: the govern query wants the scope
# entity to be governed by the scope the role sits in, and a hand-made role does not
# arrive at that. Whether a scenario may state such a grant at all is an open question;
# until it is answered this table can only say who is refused.

BUILDERS = (ungranted_user_is_refused,)
SCENARIOS: list[VFolderScenario] = [build(Seeder()) for build in BUILDERS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_vfolder(scenario: VFolderScenario, run: ScenarioRunner) -> None:
    await run(scenario)
