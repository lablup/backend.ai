"""Write specs for a model card."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.dto.manager.v2.model_card.types import ModelCardAccessLevel
from ai.backend.manager.data.model_card.types import (
    ModelCardData,
    ModelCardResourceRequirementData,
    ResourceRequirementEntry,
)
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.model_card.creators import (
    ModelCardCreator,
    ModelCardResourceRequirementCreator,
)
from ai.backend.testutils.scenario_steps import Language, Says, in_language
from bai_scenario.seeds.seeder import Naming, TestSeedFieldCreator, TestSeedRowFromThree


@dataclass(frozen=True)
class TestSeedModelCard(TestSeedRowFromThree[ProjectData, VFolderData, UserData, ModelCardData]):
    """A model card of the given project, built on the given folder by the given person."""

    title: str
    name_hint: str = "card"
    filled: bool = False

    @override
    def kind(self) -> str:
        return Says("모델 카드", english="Model card")

    @override
    def detail(self) -> str:
        return Says(
            f"프로젝트에 놓이고 vfolder 위에 추가됩니다, 제목은 '{self.title}'입니다"
            + (", 선택 항목도 모두 채웁니다" if self.filled else ""),
            english=(
                f"placed in the project and added on top of a vfolder, "
                f"titled '{in_language(self.title, Language.ENGLISH)}'"
                + (", with every optional field filled" if self.filled else "")
            ),
        )

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
            author="the-author" if self.filled else None,
            title=self.title,
            model_version="1.0" if self.filled else None,
            description="the description" if self.filled else None,
            task="text-generation" if self.filled else None,
            category="llm" if self.filled else None,
            architecture="llama" if self.filled else None,
            framework=["pytorch"] if self.filled else [],
            label=["chat"] if self.filled else [],
            license="apache-2.0" if self.filled else None,
            readme="the readme" if self.filled else None,
            access_level=ModelCardAccessLevel.INTERNAL.value,
        )


@dataclass(frozen=True)
class TestSeedCardRequirement(
    TestSeedFieldCreator[ModelCardData, ModelCardResourceRequirementData]
):
    """One minimum slot quantity the model card asks for."""

    slot_name: str
    min_quantity: str

    @override
    def kind(self) -> str:
        return Says(
            f"{self.slot_name} 최소 {self.min_quantity} 요구",
            english=f"requires at least {self.min_quantity} of {self.slot_name}",
        )

    @override
    def owner_id(self, owner: ModelCardData) -> ModelCardID:
        return owner.entity_id()

    @override
    def seed(self) -> ModelCardResourceRequirementCreator:
        return ModelCardResourceRequirementCreator(
            entry=ResourceRequirementEntry(slot_name=self.slot_name, min_quantity=self.min_quantity)
        )
