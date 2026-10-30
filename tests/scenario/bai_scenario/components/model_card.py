"""What a model card scenario table says besides the call."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.model_card import ModelCardEntityType
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.model_card.response import ModelCardNode
from ai.backend.common.dto.manager.v2.model_card.types import ModelCardAccessLevel
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.vfolder import STORAGE_HOST
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.model_card.model_card import TestSeedModelCard
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.vfolder.vfolder import TestSeedProjectVFolder

CARD_TITLE = "이미 있던 카드"


@dataclass(frozen=True)
class SomeoneHandlingCardsIn(TestSeedNest[Laid[None]]):
    """그 프로젝트에서 모델 카드에 주어진 일들을 할 수 있게 된 사용자."""

    project: Laid[ProjectData]
    someone: Laid[UserData]
    permissions: tuple[Permission, ...]

    @override
    def kind(self) -> str:
        return "모델 카드 권한 부여"

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
class ModelCardsAndACaller:
    """건드릴 모델 카드들과, 건드리려는 사람."""

    cards: tuple[ModelCardData, ...]
    caller: UserData


@dataclass(frozen=True)
class CardsInAProjectAndSomeone(Given[Any, ModelCardsAndACaller]):
    """모델 카드가 놓인 프로젝트와 사용자 한 명. 그 프로젝트에서 받은 권한은 행이 정한다.

    카드를 만든 사람과 부르는 사람은 다르다. 만든 사람이라서 통하는 길이 행에 섞이지 않는다.
    """

    count: int = 1
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        grant = (
            f"그 프로젝트에서 모델 카드에 {', '.join(str(p.name) for p in self.granted)} 권한을 받은"
            if self.granted
            else "아무 권한도 받지 않은"
        )
        return f"모델 카드 {self.count}개가 놓인 프로젝트와, {grant} {self.role.value} 한 명"

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
        cards = []
        for _ in range(self.count):
            folder = await seeding.creating_from_two(
                TestSeedProjectVFolder(host=STORAGE_HOST), project, owner
            )
            cards.append(
                await seeding.creating_from_three(
                    TestSeedModelCard(title=CARD_TITLE), project, folder, owner
                )
            )
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        if self.granted:
            await seeding.within(SomeoneHandlingCardsIn(project, caller, self.granted))
        return ModelCardsAndACaller(
            tuple(seeding.made(card) for card in cards), seeding.made(caller)
        )


@dataclass(frozen=True)
class ModelCardLook:
    """미리 만든 카드의 노드가 어떤 값으로 와야 하는지. 이름과 도메인은 미리 만든 것에서 읽는다."""

    started: datetime
    title: str = CARD_TITLE

    def verdicts(self, prefix: str, node: ModelCardNode, laid: ModelCardData) -> list[Verdict]:
        return [
            Held[UUID](f"{prefix}id", node.id, SameAs(laid.id, "미리 만든 카드")),
            Held[UUID](f"{prefix}entity_id", node.entity_id, SameAs(laid.id, "미리 만든 카드")),
            Same(f"{prefix}name", node.name, laid.name),
            Held[UUID](
                f"{prefix}vfolder_id", node.vfolder_id, SameAs(laid.vfolder_id, "카드가 얹힌 폴더")
            ),
            Same(f"{prefix}domain_name", node.domain_name, laid.domain),
            Held[UUID](
                f"{prefix}project_id",
                node.project_id,
                SameAs(laid.project_id, "카드가 놓인 프로젝트"),
            ),
            Held[UUID](
                f"{prefix}creator_id", node.creator_id, SameAs(laid.creator_id, "카드를 만든 사람")
            ),
            Same(f"{prefix}metadata.author", node.metadata.author, None),
            Same(f"{prefix}metadata.title", node.metadata.title, self.title),
            Same(f"{prefix}metadata.model_version", node.metadata.model_version, None),
            Same(f"{prefix}metadata.description", node.metadata.description, None),
            Same(f"{prefix}metadata.task", node.metadata.task, None),
            Same(f"{prefix}metadata.category", node.metadata.category, None),
            Same(f"{prefix}metadata.architecture", node.metadata.architecture, None),
            Same(f"{prefix}metadata.framework", node.metadata.framework, []),
            Same(f"{prefix}metadata.label", node.metadata.label, []),
            Same(f"{prefix}metadata.license", node.metadata.license, None),
            Same(f"{prefix}min_resource", node.min_resource, None),
            Same(f"{prefix}readme", node.readme, None),
            Same(f"{prefix}access_level", node.access_level, ModelCardAccessLevel.INTERNAL),
            Held(f"{prefix}created_at", node.created_at, WrittenByThisRun(self.started)),
            Held(f"{prefix}updated_at", node.updated_at, WrittenByThisRun(self.started)),
        ]


@dataclass(frozen=True)
class Mentions(Condition[str]):
    """이유에 이 말이 들어 있다. 이유의 나머지는 id 를 싣고 있어 실행마다 다르다."""

    phrase: str

    @override
    def says(self) -> str:
        return f"'{self.phrase}'를 담은 이유"

    @override
    def holds(self, got: str) -> bool:
        return self.phrase in got


@dataclass(frozen=True)
class NoCardIsProcessed(Then[ModelCardsAndACaller, PartialBulkPayload[ModelCardNode]]):
    """처리된 카드 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 카드 없이 대상이 모두 실패 목록에 온다"

    @override
    def look(
        self,
        laid: ModelCardsAndACaller,
        answered: Answered[PartialBulkPayload[ModelCardNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.cards)),
        ]
        for i, (failure, card) in enumerate(zip(payload.failed, laid.cards, strict=False)):
            verdicts += [
                Held[UUID](f"failed[{i}].id", failure.id, SameAs(card.id, "대상 카드의 id")),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
