"""What a model card scenario table says besides the call."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.model_card import ModelCardEntityType
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.model_card.response import (
    ModelCardNode,
    ResourceSlotEntryInfo,
    SearchModelCardsPayload,
)
from ai.backend.common.dto.manager.v2.model_card.types import ModelCardAccessLevel
from ai.backend.common.types import IntrinsicSlotNames
from ai.backend.manager.data.model_card.types import (
    ModelCardData,
    ModelCardResourceRequirementData,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Then,
    Verdict,
)
from bai_scenario.components.answers import MissingResponse, RefusedItem
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.vfolder import STORAGE_HOST
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.model_card.model_card import TestSeedCardRequirement, TestSeedModelCard
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.resource_slot.slot_type import TestSeedSlotType
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.vfolder.vfolder import TestSeedProjectVFolder

PERMISSION_REASON = "Insufficient permission"
"""권한이 없는 항목의 실패 이유가 담는 말."""

CARD_TITLE = Says("이미 있던 카드", english="a card that already existed")


@dataclass(frozen=True)
class SomeoneHandlingCardsIn(TestSeedNest[Laid[None]]):
    """그 프로젝트에서 모델 카드에 주어진 일들을 할 수 있게 된 사용자."""

    project: Laid[ProjectData]
    someone: Laid[UserData]
    permissions: tuple[Permission, ...]

    @override
    def kind(self) -> str:
        return Says("모델 카드 권한 부여", english="Grant model card permissions")

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(lambda p: ProjectID(p.id), name_hint="card-handler"), self.project
        )
        for permission in self.permissions:
            seed.adding(
                TestSeedPermission(entity_type=ModelCardEntityType(), permission=permission),
                role,
            )
        return seed.granting(
            role, self.someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class SomeoneReadingFoldersIn(TestSeedNest[Laid[None]]):
    """그 프로젝트의 vfolder 를 읽을 수 있게 된 사용자."""

    project: Laid[ProjectData]
    someone: Laid[UserData]

    @override
    def kind(self) -> str:
        return Says("vfolder 읽기 권한 부여", english="Grant vfolder read permission")

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(lambda p: ProjectID(p.id), name_hint="folder-reader"), self.project
        )
        seed.adding(
            TestSeedPermission(entity_type=VFolderEntityType(), permission=Permission.READ), role
        )
        return seed.granting(
            role, self.someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class ModelCardsAndACaller:
    """건드릴 모델 카드들과, 건드리려는 사람."""

    cards: tuple[ModelCardData, ...]
    caller: UserData
    outside: tuple[ModelCardData, ...] = ()
    """다른 프로젝트에 놓여 호출자가 아무 권한도 받지 않은 카드들."""


@dataclass(frozen=True)
class CardsInAProjectAndSomeone(Given[Any, ModelCardsAndACaller]):
    """모델 카드가 놓인 프로젝트와 사용자 한 명. 그 프로젝트에서 받은 권한은 행이 정한다.

    카드를 만든 사람과 호출자는 다르다. 만든 사람이라서 통하는 길이 행에 섞이지 않는다.
    """

    count: int = 1
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER
    outside: int = 0
    """다른 프로젝트에 놓아 호출자가 권한을 받지 않은 카드 수."""

    @override
    def describe(self) -> str:
        names = ", ".join(str(permission.name) for permission in self.granted)
        grant_ko = (
            f"그 프로젝트에서 모델 카드에 {names} 권한을 받은"
            if self.granted
            else "아무 권한도 받지 않은"
        )
        grant_en = (
            f"granted {names} on model cards in that project"
            if self.granted
            else "granted no permission"
        )
        said = Says(
            f"모델 카드 {self.count}개가 놓인 프로젝트와, {grant_ko} {self.role.value} 한 명",
            english=(
                f"a project holding {self.count} model cards and one {self.role.value} {grant_en}"
            ),
        )
        if not self.outside:
            return said
        return Says(
            f"{said}, 그리고 그 사용자가 아무 권한도 받지 않은 다른 프로젝트의 카드 "
            f"{self.outside}개",
            english=(
                f"{said.english}, and {self.outside} card in another project where that user "
                "was granted nothing"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ModelCardsAndACaller:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        owner = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(
            TestSeedProject(name_hint="model-store"), domain, policy
        )
        cards = [await self._card(seeding, project, owner) for _ in range(self.count)]
        outside = []
        if self.outside:
            elsewhere = await seeding.creating_from_two(
                TestSeedProject(name_hint="model-store"), domain, policy
            )
            outside = [await self._card(seeding, elsewhere, owner) for _ in range(self.outside)]
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        if self.granted:
            await seeding.within(SomeoneHandlingCardsIn(project, caller, self.granted))
        return ModelCardsAndACaller(
            tuple(seeding.made(card) for card in cards),
            seeding.made(caller),
            tuple(seeding.made(card) for card in outside),
        )

    async def _card(self, seeding: Any, project: Any, owner: Any) -> Any:
        folder = await seeding.creating_from_two(
            TestSeedProjectVFolder(host=STORAGE_HOST), project, owner
        )
        return await seeding.creating_from_three(
            TestSeedModelCard(title=CARD_TITLE), project, folder, owner
        )


@dataclass(frozen=True)
class ModelCardLook:
    """미리 만든 카드의 노드가 어떤 값으로 와야 하는지. 이름과 도메인은 미리 만든 것에서 읽는다."""

    started: datetime
    title: str = CARD_TITLE
    min_resource: list[ResourceSlotEntryInfo] | None = None

    def verdicts(self, prefix: str, node: ModelCardNode, laid: ModelCardData) -> list[Verdict]:
        card = Says("미리 저장한 카드", english="the card created in advance")
        return [
            Held[UUID](f"{prefix}id", node.id, SameAs(laid.id, card)),
            Held[UUID](f"{prefix}entity_id", node.entity_id, SameAs(laid.id, card)),
            Same(f"{prefix}name", node.name, laid.name),
            Held[UUID](
                f"{prefix}vfolder_id",
                node.vfolder_id,
                SameAs(
                    laid.vfolder_id,
                    Says("카드가 놓인 vfolder", english="the vfolder the card is placed on"),
                ),
            ),
            Same(f"{prefix}domain_name", node.domain_name, laid.domain),
            Held[UUID](
                f"{prefix}project_id",
                node.project_id,
                SameAs(
                    laid.project_id,
                    Says("카드가 놓인 프로젝트", english="the project the card is placed in"),
                ),
            ),
            Held[UUID](
                f"{prefix}creator_id",
                node.creator_id,
                SameAs(
                    laid.creator_id,
                    Says("카드를 만든 사람", english="the user who created the card"),
                ),
            ),
            Same(f"{prefix}metadata.author", node.metadata.author, laid.author),
            Same(f"{prefix}metadata.title", node.metadata.title, self.title),
            Same(
                f"{prefix}metadata.model_version", node.metadata.model_version, laid.model_version
            ),
            Same(f"{prefix}metadata.description", node.metadata.description, laid.description),
            Same(f"{prefix}metadata.task", node.metadata.task, laid.task),
            Same(f"{prefix}metadata.category", node.metadata.category, laid.category),
            Same(f"{prefix}metadata.architecture", node.metadata.architecture, laid.architecture),
            Same(f"{prefix}metadata.framework", node.metadata.framework, laid.framework),
            Same(f"{prefix}metadata.label", node.metadata.label, laid.label),
            Same(f"{prefix}metadata.license", node.metadata.license, laid.license),
            Same(f"{prefix}min_resource", node.min_resource, self.min_resource),
            Same(f"{prefix}readme", node.readme, laid.readme),
            Same(
                f"{prefix}access_level", node.access_level, ModelCardAccessLevel(laid.access_level)
            ),
            Held(f"{prefix}created_at", node.created_at, WrittenByThisRun(self.started)),
            Held(f"{prefix}updated_at", node.updated_at, WrittenByThisRun(self.started)),
        ]


@dataclass(frozen=True)
class TheOutsideCardIsRefused(Then[ModelCardsAndACaller, PartialBulkPayload[ModelCardNode]]):
    """권한이 있는 카드는 처리된 목록에 오고, 다른 프로젝트의 카드만 권한이 없다는 이유로 실패
    목록에 온다."""

    started: datetime
    title: str = CARD_TITLE

    @override
    def says(self) -> str:
        return Says(
            "권한이 있는 카드는 모두 처리된 목록에 오고, 다른 프로젝트의 카드만 권한이 없다는 "
            "이유로 실패 목록에 옵니다",
            english=(
                "every card the caller may touch comes back in the processed list, and only the "
                "card in the other project comes back in the failed list for lack of permission"
            ),
        )

    @override
    def look(
        self,
        laid: ModelCardsAndACaller,
        answered: Answered[PartialBulkPayload[ModelCardNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        look = ModelCardLook(self.started, title=self.title)
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.cards))]
        for i, (node, card) in enumerate(zip(payload.successes, laid.cards, strict=False)):
            verdicts += look.verdicts(f"successes[{i}].", node, card)
        verdicts.append(Same("failed count", len(payload.failed), len(laid.outside)))
        for i, (failure, card) in enumerate(zip(payload.failed, laid.outside, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        card.id,
                        Says("다른 프로젝트의 카드", english="the card in the other project"),
                    ),
                ),
                RefusedItem(
                    f"failed[{i}].message", NotEnoughPermission, PERMISSION_REASON, failure.message
                ),
            ]
        return verdicts


SEARCH_TITLE = Says("검색에 걸리는 카드", english="a card the search finds")
OTHER_TITLE = Says("검색에 걸리지 않는 카드", english="a card the search skips")


@dataclass(frozen=True)
class ProjectCards:
    """두 프로젝트에 놓인 카드들과, 호출자.

    ``found`` 는 첫 프로젝트에서 제목이 검색에 걸리는 카드 셋(만든 순서), ``skipped`` 는 같은
    프로젝트의 제목이 걸리지 않는 카드, ``elsewhere`` 는 다른 프로젝트의 제목이 걸리는 카드다.
    카드마다 cpu 최소 요구 하나가 있다.
    """

    project: ProjectData
    other_project: ProjectData
    found: tuple[ModelCardData, ModelCardData, ModelCardData]
    skipped: ModelCardData
    elsewhere: ModelCardData
    requirements: tuple[ModelCardResourceRequirementData, ...]
    caller: UserData

    def cards(self) -> tuple[ModelCardData, ...]:
        return (*self.found, self.skipped, self.elsewhere)

    def entries(self, card: ModelCardData) -> list[ResourceSlotEntryInfo]:
        return [
            ResourceSlotEntryInfo(resource_type=r.slot_name, quantity=r.min_quantity)
            for r in self.requirements
            if r.model_card_id == card.entity_id()
        ]

    def look(self, started: datetime, card: ModelCardData) -> ModelCardLook:
        return ModelCardLook(
            started,
            title=OTHER_TITLE if card.id == self.skipped.id else SEARCH_TITLE,
            min_resource=self.entries(card),
        )


@dataclass(frozen=True)
class TwoProjectsOfCardsAndSomeone(Given[Any, ProjectCards]):
    """모델 카드가 놓인 프로젝트 둘과 사용자 한 명. 첫 프로젝트에서 받은 권한은 행이 정한다.

    사용자는 첫 프로젝트에서만 권한을 받고, 카드를 만든 사람과 다르다. 모든 카드가 선택
    항목을 채우고 cpu 최소 요구를 하나씩 갖는다.
    """

    granted: tuple[Permission, ...] = ()
    reads_folders: bool = False

    @override
    def describe(self) -> str:
        names = ", ".join(str(permission.name) for permission in self.granted)
        grant_ko = (
            f"첫 프로젝트에서 모델 카드에 {names} 권한을 받은"
            if self.granted
            else "아무 권한도 받지 않은"
        )
        grant_en = (
            f"granted {names} on model cards in the first project"
            if self.granted
            else "granted no permission"
        )
        folders_ko = ", 그 프로젝트의 vfolder 읽기도 받은" if self.reads_folders else ""
        folders_en = " and vfolder read in it" if self.reads_folders else ""
        return Says(
            f"모델 카드가 놓인 프로젝트 둘과, {grant_ko}{folders_ko} user 한 명",
            english=(f"two projects holding model cards and one user {grant_en}{folders_en}"),
        )

    @override
    async def lay(self, seeding: Any) -> ProjectCards:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        owner = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(
            TestSeedProject(name_hint="model-store"), domain, policy
        )
        other_project = await seeding.creating_from_two(
            TestSeedProject(name_hint="other-store"), domain, policy
        )
        laid_cards = []
        for where, title in (
            (project, SEARCH_TITLE),
            (project, SEARCH_TITLE),
            (project, SEARCH_TITLE),
            (project, OTHER_TITLE),
            (other_project, SEARCH_TITLE),
        ):
            folder = await seeding.creating_from_two(
                TestSeedProjectVFolder(host=STORAGE_HOST), where, owner
            )
            laid_cards.append(
                await seeding.creating_from_three(
                    TestSeedModelCard(title=title, filled=True), where, folder, owner
                )
            )
        slot = await seeding.once(TestSeedSlotType(IntrinsicSlotNames.CPU))
        slot_name = seeding.made(slot).slot_name
        requirements = []
        for number, card in enumerate(laid_cards, start=1):
            requirements.append(
                await seeding.adding(
                    TestSeedCardRequirement(slot_name=slot_name, min_quantity=str(number)), card
                )
            )
        caller = await seeding.within(SomeoneOf(domain))
        if self.granted:
            await seeding.within(SomeoneHandlingCardsIn(project, caller, self.granted))
        if self.reads_folders:
            await seeding.within(SomeoneReadingFoldersIn(project, caller))
        cards = [seeding.made(card) for card in laid_cards]
        return ProjectCards(
            project=seeding.made(project),
            other_project=seeding.made(other_project),
            found=(cards[0], cards[1], cards[2]),
            skipped=cards[3],
            elsewhere=cards[4],
            requirements=tuple(seeding.made(r) for r in requirements),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheFoundPage(Then[ProjectCards, SearchModelCardsPayload]):
    """찾은 카드는 ``found`` 에서 고른 것들뿐이고, 다른 카드는 응답에도 건수에도 없다."""

    started: datetime
    picked: tuple[int, ...]
    total_count: int
    has_next_page: bool

    @override
    def says(self) -> str:
        return Says(
            "필터에 걸리고 범위 안에 있는 카드만 정렬 순서대로 한 페이지에 옵니다. 범위 밖 카드와 "
            "필터에 걸리지 않는 카드는 응답에도 건수에도 없습니다",
            english=(
                "only the cards inside the scope that the filter matches come back in the "
                "requested order in one page, and the card outside the scope and the card the "
                "filter skips are in neither the page nor the count"
            ),
        )

    @override
    def look(
        self, laid: ProjectCards, answered: Answered[SearchModelCardsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [Same("items count", len(payload.items), len(self.picked))]
        for i, (node, index) in enumerate(zip(payload.items, self.picked, strict=False)):
            card = laid.found[index]
            verdicts += laid.look(self.started, card).verdicts(f"items[{i}].", node, card)
        verdicts += [
            Same("total_count", payload.total_count, self.total_count),
            Same("has_next_page", payload.has_next_page, self.has_next_page),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        return verdicts
