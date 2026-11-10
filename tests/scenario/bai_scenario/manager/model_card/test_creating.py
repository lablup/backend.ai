"""모델 카드 생성."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput,
    ResourceSlotEntryInput,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    ModelCardNode,
    ResourceSlotEntryInfo,
)
from ai.backend.common.dto.manager.v2.model_card.types import ModelCardAccessLevel
from ai.backend.common.types import IntrinsicSlotNames
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import ModelCardConflict
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.model_card import CARD_TITLE, SomeoneHandlingCardsIn
from bai_scenario.components.vfolder import STORAGE_HOST
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.model_card.model_card import TestSeedModelCard
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.resource_slot.slot_type import TestSeedSlotType
from bai_scenario.seeds.vfolder.vfolder import TestSeedProjectVFolder

type Created = ModelCardNode

NAME = "llama-card"
AUTHOR = Says("모델을 만든 사람", english="the model author")
TITLE = Says("새 카드", english="a new card")
VERSION = "1.0"
DESCRIPTION = Says("새로 등록한 카드", english="a newly registered card")
TASK = "text-generation"
CATEGORY = "llm"
ARCHITECTURE = "transformer"
FRAMEWORK = ["pytorch"]
LABEL = ["chat"]
LICENSE = "apache-2.0"
README = Says("카드 설명서", english="the card readme")
CPU_MINIMUM = "2"


@dataclass(frozen=True)
class ACardPlace:
    """카드를 놓을 프로젝트와 vfolder, 만들려는 사람. `existing`은 이미 놓인 카드다."""

    domain: DomainData
    project: ProjectData
    folder: VFolderData
    slot: ResourceSlotTypeData
    caller: UserData
    existing: ModelCardData | None


@dataclass(frozen=True)
class AFolderInAProjectAndSomeone(Given[Any, ACardPlace]):
    """vfolder 가 놓인 프로젝트와 그 프로젝트에서 주어진 권한을 받은 사용자 한 명."""

    granted: tuple[Permission, ...]
    existing: bool = False

    @override
    def describe(self) -> str:
        names = ", ".join(str(permission.name) for permission in self.granted)
        said = Says(
            f"vfolder 가 놓인 프로젝트와, 그 프로젝트에서 모델 카드에 {names} 권한을 받은 "
            "사용자 한 명",
            english=(
                "a project holding a vfolder and one user granted "
                f"{names} on model cards in that project"
            ),
        )
        if not self.existing:
            return said
        return Says(
            f"{said}, 그리고 그 프로젝트에 이미 놓인 카드 하나",
            english=f"{said.english}, and one card already placed in that project",
        )

    @override
    async def lay(self, seeding: Any) -> ACardPlace:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(
            TestSeedProject(name_hint="model-store"), domain, policy
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        folder = await seeding.creating_from_two(
            TestSeedProjectVFolder(host=STORAGE_HOST), project, caller
        )
        slot = await seeding.creating(TestSeedSlotType(IntrinsicSlotNames.CPU))
        existing = None
        if self.existing:
            existing = await seeding.creating_from_three(
                TestSeedModelCard(title=CARD_TITLE), project, folder, caller
            )
        await seeding.within(SomeoneHandlingCardsIn(project, caller, self.granted))
        return ACardPlace(
            seeding.made(domain),
            seeding.made(project),
            seeding.made(folder),
            seeding.made(slot),
            seeding.made(caller),
            seeding.made(existing) if existing is not None else None,
        )


@dataclass(frozen=True)
class CreatingACard(When[ACardPlace, ModelCardAdapter, Created]):
    """선택 항목까지 모두 채워 카드를 만든다. `existing`이 있으면 그 이름을 쓴다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ACardPlace) -> str:
        if laid.existing is not None:
            return Says(
                f"{laid.caller.username}이 이미 놓인 카드와 같은 이름으로 카드를 만듭니다",
                english=(
                    f"{laid.caller.username} creates a card under the name of the card "
                    "already there"
                ),
            )
        return Says(
            f"{laid.caller.username}이 선택 항목까지 모두 채워 카드를 만듭니다",
            english=f"{laid.caller.username} creates a card with every optional field filled",
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ACardPlace) -> Created:
        name = laid.existing.name if laid.existing is not None else NAME
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateModelCardInput(
                    name=name,
                    vfolder_id=laid.folder.id,
                    model_store_project_id=laid.project.id,
                    domain_name=laid.domain.name,
                    author=AUTHOR,
                    title=TITLE,
                    model_version=VERSION,
                    description=DESCRIPTION,
                    task=TASK,
                    category=CATEGORY,
                    architecture=ARCHITECTURE,
                    framework=FRAMEWORK,
                    label=LABEL,
                    license=LICENSE,
                    min_resource=[
                        ResourceSlotEntryInput(
                            resource_type=laid.slot.slot_name, quantity=CPU_MINIMUM
                        )
                    ],
                    readme=README,
                    access_level=ModelCardAccessLevel.PUBLIC,
                )
            )
        return payload.model_card


@dataclass(frozen=True)
class TheCardAsAsked(Then[ACardPlace, Created]):
    """요청에 채운 값이 모두 그대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "요청에 채운 값으로 프로젝트에 놓이고 요청한 사람이 만든 카드가 옵니다",
            english=(
                "a card placed in the project, created by the requesting user, comes back with "
                "every value the request filled"
            ),
        )

    @override
    def look(self, laid: ACardPlace, answered: Answered[Created]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return [
            Skipped("id", Says("데이터베이스가 만든다", english="the database generates it")),
            Held[UUID](
                "entity_id",
                node.entity_id,
                SameAs(node.id, Says("응답의 id", english="the id of the answer")),
            ),
            Same("name", node.name, NAME),
            Held[UUID](
                "vfolder_id",
                node.vfolder_id,
                SameAs(laid.folder.id, Says("요청한 vfolder", english="the requested vfolder")),
            ),
            Same("domain_name", node.domain_name, laid.domain.name),
            Held[UUID](
                "project_id",
                node.project_id,
                SameAs(laid.project.id, Says("요청한 프로젝트", english="the requested project")),
            ),
            Held[UUID](
                "creator_id",
                node.creator_id,
                SameAs(laid.caller.id, Says("요청한 사람", english="the requesting user")),
            ),
            Same("metadata.author", node.metadata.author, AUTHOR),
            Same("metadata.title", node.metadata.title, TITLE),
            Same("metadata.model_version", node.metadata.model_version, VERSION),
            Same("metadata.description", node.metadata.description, DESCRIPTION),
            Same("metadata.task", node.metadata.task, TASK),
            Same("metadata.category", node.metadata.category, CATEGORY),
            Same("metadata.architecture", node.metadata.architecture, ARCHITECTURE),
            Same("metadata.framework", node.metadata.framework, FRAMEWORK),
            Same("metadata.label", node.metadata.label, LABEL),
            Same("metadata.license", node.metadata.license, LICENSE),
            Same(
                "min_resource",
                node.min_resource,
                [ResourceSlotEntryInfo(resource_type=laid.slot.slot_name, quantity=CPU_MINIMUM)],
            ),
            Same("readme", node.readme, README),
            Same("access_level", node.access_level, ModelCardAccessLevel.PUBLIC),
            Held("created_at", node.created_at, WrittenByThisRun(self.started)),
            Held("updated_at", node.updated_at, WrittenByThisRun(self.started)),
        ]


@dataclass(frozen=True)
class AUserGrantedCreateMakesACard(
    Scenario[TestSeedingSession, ACardPlace, ModelCardAdapter, Created]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-create-in-the-project-makes-a-model-card"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 생성과 읽기 권한을 받은 사용자가 카드를 만들면, 그 프로젝트에 "
            "놓이고 그 사용자가 만든 카드가 요청한 값과 최소 자원으로 옵니다",
            english=(
                "when a user granted create and read permission on model cards in the project "
                "creates a card, a card placed in that project and created by that user comes "
                "back with the requested values and minimum resources"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACardPlace]:
        return AFolderInAProjectAndSomeone(granted=(Permission.CREATE, Permission.READ))

    @override
    def when(self) -> When[ACardPlace, ModelCardAdapter, Created]:
        return CreatingACard()

    @override
    def then(self) -> Then[ACardPlace, Created]:
        return TheCardAsAsked(started=self.started)


@dataclass(frozen=True)
class AUserWithoutCreateMayNotMakeACard(
    Scenario[TestSeedingSession, ACardPlace, ModelCardAdapter, Created]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-make-a-model-card"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 읽기 권한만 받은 사용자가 카드를 만들려 하면 권한이 없다는 "
            "이유로 거부됩니다",
            english=(
                "when a user granted only read permission on model cards in the project tries "
                "to create a card, the call is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACardPlace]:
        return AFolderInAProjectAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ACardPlace, ModelCardAdapter, Created]:
        return CreatingACard()

    @override
    def then(self) -> Then[ACardPlace, Created]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ATakenNameIsRefused(Scenario[TestSeedingSession, ACardPlace, ModelCardAdapter, Created]):
    @override
    def summary(self) -> str:
        return "a-name-taken-in-the-project-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 생성과 읽기 권한을 받은 사용자가 그 프로젝트에 이미 있는 카드와 "
            "같은 이름으로 카드를 만들려 하면 이름이 겹친다는 이유로 거부됩니다",
            english=(
                "when a user granted create and read permission on model cards in the project "
                "creates a card under the name of a card already in that project, the call is "
                "rejected as a name conflict"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACardPlace]:
        return AFolderInAProjectAndSomeone(
            granted=(Permission.CREATE, Permission.READ), existing=True
        )

    @override
    def when(self) -> When[ACardPlace, ModelCardAdapter, Created]:
        return CreatingACard()

    @override
    def then(self) -> Then[ACardPlace, Created]:
        return TheCallIsRefused(ModelCardConflict)


type CardStep = Scenario[TestSeedingSession, ACardPlace, ModelCardAdapter, Created]

SCENARIOS: list[CardStep] = [
    AUserGrantedCreateMakesACard(started=datetime.now(UTC)),
    AUserWithoutCreateMayNotMakeACard(),
    ATakenNameIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CardStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
