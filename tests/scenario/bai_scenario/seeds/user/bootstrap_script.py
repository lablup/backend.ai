"""Write specs for the bootstrap scripts a user holds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript, BootstrapScriptID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.bootstrap_script.types import (
    BootstrapScriptRevisionData,
    UserDefaultBootstrapScriptData,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.bootstrap_script.creators import BootstrapScriptCreator
from ai.backend.manager.models.bootstrap_script.upserters import (
    UserDefaultBootstrapScriptUpserter,
)
from ai.backend.manager.models.bootstrap_script_revision.creators import (
    BootstrapScriptRevisionCreator,
)
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.ops import TestSeedOps
from bai_scenario.seeds.seeder import TestSeedField, TestSeedFieldUpserter


@dataclass(frozen=True)
class TestSeedBootstrapScriptOf(TestSeedField[UserData, BootstrapScriptRevisionData]):
    """A script the user holds and its first revision, which the user wrote.

    The manager writes the two rows in one operation, so this seed takes both writes.
    """

    script: str

    @override
    def kind(self) -> str:
        return Says(
            f"revision 1 의 내용이 {self.script!r} 인 bootstrap script 하나를 갖습니다",
            english=f"holds one bootstrap script whose revision 1 holds {self.script!r}",
        )

    @override
    def owner_id(self, owner: UserData) -> UserID:
        return UserID(owner.id)

    @override
    async def write(self, ops: TestSeedOps, owner_id: UserID) -> BootstrapScriptRevisionData:
        created = await ops.create_field(owner_id, BootstrapScriptCreator())
        return await ops.create_dangling_field(
            BootstrapScriptRevisionCreator(
                script_id=created.id, script=BootstrapScript(self.script), creator_id=owner_id
            )
        )


@dataclass(frozen=True)
class TestSeedDefaultBootstrapScriptOf(
    TestSeedFieldUpserter[UserData, UserDefaultBootstrapScriptData]
):
    """The user's default pointed at a script an earlier row laid."""

    script_id: BootstrapScriptID

    @override
    def kind(self) -> str:
        return Says(
            "그 bootstrap script 를 default 로 지정합니다",
            english="sets that bootstrap script as the default",
        )

    @override
    def owner_id(self, owner: UserData) -> UserID:
        return UserID(owner.id)

    @override
    def seed(self) -> UserDefaultBootstrapScriptUpserter:
        return UserDefaultBootstrapScriptUpserter(script_id=self.script_id)
