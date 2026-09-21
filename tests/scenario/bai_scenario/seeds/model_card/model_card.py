"""Write specs for a model card and the minimum resources it asks for.

A card sits on a folder of a project and joins that project and the person who made
it. What it needs to run is a field row per slot, laid under the card.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
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
from bai_scenario.seeds.seeder import Naming, SeedField, SeedRowFromThree


@dataclass(frozen=True)
class SeedModelCard(SeedRowFromThree[ProjectData, VFolderData, UserData, ModelCardData]):
    """A card of the given project, on the given folder, made by the given person."""

    name_hint: str = "card"
    access_level: ModelCardAccessLevel = ModelCardAccessLevel.INTERNAL

    @override
    def kind(self) -> str:
        return "모델 카드"

    @override
    def detail(self) -> str:
        return f"접근 수준은 {self.access_level.value}, 요구 자원은 따로 심는다"

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
            title=None,
            model_version=None,
            description=None,
            task=None,
            category=None,
            architecture=None,
            framework=[],
            label=[],
            license=None,
            readme=None,
            access_level=self.access_level.value,
        )


@dataclass(frozen=True)
class SeedRequirement(SeedField[ModelCardData, ModelCardResourceRequirementData]):
    """The least of one slot the card needs to run."""

    slot: str
    at_least: Decimal

    @override
    def kind(self) -> str:
        return f"{self.slot} 최소 {self.at_least} 필요"

    @override
    def owner_id(self, owner: ModelCardData) -> ModelCardID:
        return ModelCardID(owner.id)

    @override
    def seed(self) -> ModelCardResourceRequirementCreator:
        return ModelCardResourceRequirementCreator(
            entry=ResourceRequirementEntry(slot_name=self.slot, min_quantity=str(self.at_least))
        )
