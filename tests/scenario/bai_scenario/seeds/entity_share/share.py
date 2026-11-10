"""Write specs for a share: the offer, and its recipient taking it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.entity_share.creators import EntityShareCreator
from ai.backend.manager.models.entity_share.updaters import EntityShareAcceptUpdater
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRowFromThree, TestSeedShareAcceptance


@dataclass(frozen=True)
class TestSeedVFolderShare(TestSeedRowFromThree[UserData, VFolderData, UserData, EntityShareData]):
    """The first person offers the folder to the second, under ``cap``."""

    cap: Permission | None = None
    name_hint: str = "share"

    @override
    def kind(self) -> str:
        return Says("vfolder 공유 제안", english="vfolder share offer")

    @override
    def detail(self) -> str:
        if self.cap is None:
            return Says(
                "권한 상한 없이 제안되었고, 아직 응답하지 않았습니다",
                english="offered with no ceiling on the permissions, not answered yet",
            )
        return Says(
            f"{self.cap.name} 권한으로 제안되었고, 아직 응답하지 않았습니다",
            english=f"offered under the {self.cap.name} permission, not answered yet",
        )

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(
        self, name: str, first: UserData, second: VFolderData, third: UserData
    ) -> EntityShareCreator:
        return EntityShareCreator(
            sharer_user_id=UserID(first.id),
            target=VFolderUUID(second.id),
            recipient=UserID(third.id),
            permission_cap=self.cap,
        )


@dataclass(frozen=True)
class TestSeedShareTaken(TestSeedShareAcceptance[EntityShareData]):
    """The recipient the offer names takes it."""

    @override
    def kind(self) -> str:
        return Says("받는 사람이 받아들임", english="the recipient accepts it")

    @override
    def seed(self, offer: EntityShareData) -> EntityShareAcceptUpdater:
        if offer.recipient is None:
            raise LookupError("an offer to an address has no recipient to take it")
        return EntityShareAcceptUpdater(share_id=offer.id, answering_scope=offer.recipient)
