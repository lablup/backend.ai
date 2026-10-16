"""Write specs for a model card."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.dto.manager.v2.model_card.types import ModelCardAccessLevel
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.model_card.creators import ModelCardCreator
from bai_scenario.seeds.seeder import Naming, TestSeedRowFromThree


@dataclass(frozen=True)
class TestSeedModelCard(TestSeedRowFromThree[ProjectData, VFolderData, UserData, ModelCardData]):
    """A model card of the given project, built on the given folder by the given person."""

    title: str
    name_hint: str = "card"

    @override
    def kind(self) -> str:
        return "모델 카드"

    @override
    def detail(self) -> str:
        return f"프로젝트에 놓이고 폴더 위에 얹힌다, 제목 '{self.title}'"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(
        self, name: str, first: ProjectData, second: VFolderData, third: UserData
    ) -> ModelCardCreator:
        return ModelCardCreator(
            name=name,
            vfolder_id=VFolderUUID(second.id),
            domain=first.domain_name,
            project_id=ProjectID(first.id),
            creator_id=UserID(third.id),
            author=None,
            title=self.title,
            model_version=None,
            description=None,
            task=None,
            category=None,
            architecture=None,
            framework=[],
            label=[],
            license=None,
            readme=None,
            access_level=ModelCardAccessLevel.INTERNAL.value,
        )
