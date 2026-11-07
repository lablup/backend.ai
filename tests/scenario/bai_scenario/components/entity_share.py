"""What an entity share scenario table says besides the call.

A share lends a folder of a project to a person. The lending side is granted on the
project, where the folder lives, and the receiving side answers in their own scope. A
table needs the folder, the offer, both people, and which of them calls.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.entity_share import EntityShareEntityType
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.entity_share.response import (
    EntityShareNode,
    SearchEntitySharesPayload,
)
from ai.backend.common.dto.manager.v2.entity_share.types import EntityShareStatusDTO
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.entity_share.share import TestSeedShareTaken, TestSeedVFolderShare
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.vfolder.vfolder import TestSeedProjectVFolder

HOST = "local:volume1"
"""폴더가 놓이는 저장소."""
SHARER_ON_PROJECT = (Permission.CREATE, Permission.READ, Permission.SOFT_DELETE)
"""폴더를 빌려주는 사람이 프로젝트에서 갖는 권한."""
RECIPIENT_IN_OWN_SCOPE = (Permission.READ, Permission.UPDATE, Permission.SOFT_DELETE)
"""빌린 사람이 자기 스코프에서 갖는 권한."""


class Side(enum.Enum):
    """누가 부르는지."""

    SHARER = "sharer"
    RECIPIENT = "recipient"
    SOMEBODY = "somebody"


@dataclass(frozen=True)
class ASharedFolderAndACaller:
    """폴더 하나, 그 폴더에 걸린 공유, 빌려준 사람, 빌린 사람, 그리고 부르는 사람."""

    folder: VFolderData
    share: EntityShareData | None
    sharer: UserData
    recipient: UserData
    caller: UserData


@dataclass(frozen=True)
class SomeoneGrantedOnTheProject(TestSeedNest[Laid[UserData]]):
    """그 프로젝트에서 공유에 정해진 권한을 갖는 사용자."""

    domain: Laid[DomainData]
    project: Laid[ProjectData]
    granted: tuple[Permission, ...]

    @override
    def kind(self) -> str:
        return Says(
            "프로젝트 범위의 공유 권한을 받은 사용자 준비",
            english="Prepare a user granted share permissions in the project scope",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            TestSeedRole(lambda p: ProjectID(p.id), name_hint="share-lender"), self.project
        )
        for one in self.granted:
            seed.adding(
                TestSeedPermission(entity_type=EntityShareEntityType(), permission=one), role
            )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


@dataclass(frozen=True)
class SomeoneAnsweringInTheirOwnScope(TestSeedNest[Laid[UserData]]):
    """자기 스코프에서 공유에 답할 수 있는 사용자."""

    user: Laid[UserData]
    granted: tuple[Permission, ...]

    @override
    def kind(self) -> str:
        return Says(
            "자기 스코프의 공유 권한을 받은 사용자 준비",
            english="Prepare a user granted share permissions in their own scope",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        role = seed.creating_from(
            TestSeedRole(lambda u: UserID(u.id), name_hint="share-recipient"), self.user
        )
        for one in self.granted:
            seed.adding(
                TestSeedPermission(entity_type=EntityShareEntityType(), permission=one), role
            )
        seed.granting(role, self.user, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return self.user


def _who(side: Side, sharer: str, recipient: str, somebody: str) -> str:
    match side:
        case Side.SHARER:
            return sharer
        case Side.RECIPIENT:
            return recipient
        case Side.SOMEBODY:
            return somebody


@dataclass(frozen=True)
class ASharedFolderAndSomeone(Given[Any, ASharedFolderAndACaller]):
    """프로젝트 폴더 하나와 두 사람.

    ``offered`` 면 폴더를 두 번째 사람에게 빌려주는 제안이 서 있고, ``taken`` 면 그 제안을
    받아들여 공유가 서 있다. ``elsewhere`` 면 범위 밖의 폴더 하나와, 받는 사람이 그 폴더를
    빌려주는 제안이 함께 서 있다. ``who`` 가 부르는 사람이다.
    """

    who: Side = Side.SHARER
    offered: bool = True
    taken: bool = False
    elsewhere: bool = False
    cap: Permission | None = None
    sharer_granted: tuple[Permission, ...] = SHARER_ON_PROJECT
    recipient_granted: tuple[Permission, ...] = RECIPIENT_IN_OWN_SCOPE

    @override
    def describe(self) -> str:
        who_ko = _who(self.who, "폴더를 빌려주는 사람", "폴더를 빌린 사람", "아무 관련 없는 사람")
        who_en = _who(
            self.who,
            "the person lending the folder",
            "the person the folder is lent to",
            "someone unrelated",
        )
        outside_ko = "범위 밖의 폴더 하나와 받는 사람이 내는 제안 하나, " if self.elsewhere else ""
        outside_en = (
            "one more folder outside the scope whose offer the recipient makes, "
            if self.elsewhere
            else ""
        )
        if self.taken:
            return Says(
                f"{outside_ko}프로젝트 폴더 하나와, 다른 사람에게 빌려준 공유, 그리고 {who_ko}",
                english=(
                    f"{outside_en}one project folder with a share lent to another person, "
                    f"and {who_en}"
                ),
            )
        if self.offered:
            return Says(
                f"{outside_ko}프로젝트 폴더 하나와, 다른 사람에게 보낸 제안, 그리고 {who_ko}",
                english=(
                    f"{outside_en}one project folder with an offer to another person, and {who_en}"
                ),
            )
        return Says(
            f"{outside_ko}프로젝트 폴더 하나와 두 사람, 그리고 {who_ko}",
            english=f"{outside_en}one project folder and two people, and {who_en}",
        )

    @override
    async def lay(self, seeding: Any) -> ASharedFolderAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(name_hint="team"), domain, policy)
        sharer = (
            await seeding.within(SomeoneGrantedOnTheProject(domain, project, self.sharer_granted))
            if self.sharer_granted
            else await seeding.within(SomeoneOf(domain))
        )
        if self.sharer_granted:
            await seeding.within(SomeoneAnsweringInTheirOwnScope(sharer, (Permission.READ,)))
        folder = await seeding.creating_from_two(TestSeedProjectVFolder(host=HOST), project, sharer)
        recipient = await seeding.within(SomeoneOf(domain))
        if self.recipient_granted:
            await seeding.within(SomeoneAnsweringInTheirOwnScope(recipient, self.recipient_granted))
        share: Laid[EntityShareData] | None = None
        if self.offered or self.taken:
            share = await seeding.creating_from_three(
                TestSeedVFolderShare(cap=self.cap),
                sharer,
                folder,
                recipient,
            )
        if self.taken:
            if share is None:
                raise LookupError("a taken share needs the offer it settled")
            await seeding.accepting(TestSeedShareTaken(), share)
        if self.elsewhere:
            other_folder = await seeding.creating_from_two(
                TestSeedProjectVFolder(host=HOST, name_hint="other-folder"), project, recipient
            )
            await seeding.creating_from_three(
                TestSeedVFolderShare(cap=self.cap, name_hint="other-share"),
                recipient,
                other_folder,
                sharer,
            )
        caller: Laid[UserData]
        match self.who:
            case Side.SHARER:
                caller = sharer
            case Side.RECIPIENT:
                caller = recipient
            case Side.SOMEBODY:
                caller = await seeding.within(SomeoneOf(domain))
        return ASharedFolderAndACaller(
            folder=seeding.made(folder),
            share=seeding.made(share) if share is not None else None,
            sharer=seeding.made(sharer),
            recipient=seeding.made(recipient),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ShareLook:
    """공유 노드가 어떤 값으로 와야 하는지."""

    started: datetime
    laid: EntityShareData | None

    def verdicts(
        self,
        prefix: str,
        node: EntityShareNode,
        folder: VFolderData,
        sharer: UserData,
        recipient: UserData,
        status: EntityShareStatusDTO,
    ) -> list[Verdict]:
        written = WrittenByThisRun(self.started)
        verdicts: list[Verdict] = [
            Held[UUID | None](
                f"{prefix}sharer_user_id",
                node.sharer_user_id,
                SameAs[UUID | None](
                    sharer.id,
                    Says(
                        "미리 만든 빌려준 사람의 id",
                        english="the id of the person lending the folder",
                    ),
                ),
            ),
            Same(
                f"{prefix}recipient_entity_type",
                node.recipient_entity_type.name() if node.recipient_entity_type else None,
                "user",
            ),
            Held[UUID | None](
                f"{prefix}recipient_entity_id",
                node.recipient_entity_id,
                SameAs[UUID | None](
                    recipient.id,
                    Says(
                        "미리 만든 빌린 사람의 id",
                        english="the id of the person the folder is lent to",
                    ),
                ),
            ),
            Same(f"{prefix}recipient_email", node.recipient_email, None),
            Same(f"{prefix}target_entity_type", node.target_entity_type.name(), "vfolder"),
            Held[UUID](
                f"{prefix}target_entity_id",
                node.target_entity_id,
                SameAs(
                    folder.id,
                    Says("미리 만든 폴더의 id", english="the id of the folder laid in advance"),
                ),
            ),
            Same(f"{prefix}permissions", node.permissions, []),
            Same(f"{prefix}status", node.status.value, status.value),
            Same(f"{prefix}expires_at", node.expires_at, None),
            Held(f"{prefix}created_at", node.created_at, written),
            Held(f"{prefix}updated_at", node.updated_at, written),
        ]
        if self.laid is None:
            return [
                *verdicts,
                Skipped(
                    f"{prefix}id",
                    Says("데이터베이스가 생성합니다", english="the database generates it"),
                ),
                Held[UUID](
                    f"{prefix}entity_id",
                    node.entity_id,
                    SameAs(
                        node.id,
                        Says(
                            "같은 응답이 담은 공유의 id",
                            english="the id of the share in the same answer",
                        ),
                    ),
                ),
            ]
        return [
            *verdicts,
            Held[UUID](
                f"{prefix}id",
                node.id,
                SameAs(
                    self.laid.id,
                    Says(
                        "미리 만든 공유의 id",
                        english="the id of the share laid in advance",
                    ),
                ),
            ),
            Held[UUID](
                f"{prefix}entity_id",
                node.entity_id,
                SameAs(
                    self.laid.id,
                    Says(
                        "미리 만든 공유의 id",
                        english="the id of the share laid in advance",
                    ),
                ),
            ),
        ]


@dataclass(frozen=True)
class TheShareNode(Then[ASharedFolderAndACaller, EntityShareNode]):
    """그 공유가 정해진 상태로 통째로 온다."""

    started: datetime
    status: EntityShareStatusDTO
    fresh: bool = False

    @override
    def says(self) -> str:
        return Says(
            "그 공유 전체가 응답으로 옵니다",
            english="the whole share comes back",
        )

    @override
    def look(
        self, laid: ASharedFolderAndACaller, answered: Answered[EntityShareNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return ShareLook(self.started, None if self.fresh else laid.share).verdicts(
            "", node, laid.folder, laid.sharer, laid.recipient, self.status
        )


@dataclass(frozen=True)
class TheSharesComeBack(Then[ASharedFolderAndACaller, list[EntityShareNode | Exception | None]]):
    """그 공유가 노드로 온다. id 로 읽으면 없는 id 자리도 권한 검사를 지나 거부된다."""

    started: datetime
    missing: bool = False

    @override
    def says(self) -> str:
        if self.missing:
            return Says(
                "미리 만든 공유는 노드로, 없는 id 자리는 권한 부족으로 옵니다",
                english=(
                    "the share laid in advance comes back as a node and the unknown id entry "
                    "is rejected for lack of permission"
                ),
            )
        return Says(
            "미리 만든 공유가 노드로 옵니다",
            english="the share laid in advance comes back as a node",
        )

    @override
    def look(
        self,
        laid: ASharedFolderAndACaller,
        answered: Answered[list[EntityShareNode | Exception | None]],
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        expected = 1 + (1 if self.missing else 0)
        verdicts: list[Verdict] = [Same("length", len(loaded), expected)]
        if len(loaded) != expected:
            return verdicts
        first = loaded[0]
        if isinstance(first, EntityShareNode):
            verdicts += ShareLook(self.started, laid.share).verdicts(
                "[0].",
                first,
                laid.folder,
                laid.sharer,
                laid.recipient,
                EntityShareStatusDTO.PENDING,
            )
        else:
            verdicts.append(Same("[0]", type(first).__name__, "EntityShareNode"))
        if self.missing:
            last = loaded[1]
            verdicts.append(
                Same(
                    "[1] denied",
                    type(last).__name__ if isinstance(last, Exception) else None,
                    "NotEnoughPermission",
                )
            )
        return verdicts


@dataclass(frozen=True)
class TheSearchedShares(Then[ASharedFolderAndACaller, SearchEntitySharesPayload]):
    """그 공유가 통째로 온다."""

    started: datetime
    status: EntityShareStatusDTO = EntityShareStatusDTO.PENDING

    @override
    def says(self) -> str:
        return Says(
            "미리 만든 공유가 통째로 옵니다",
            english="the share laid in advance comes back whole",
        )

    @override
    def look(
        self, laid: ASharedFolderAndACaller, answered: Answered[SearchEntitySharesPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("items count", len(page.items), 1),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
        for node in page.items:
            verdicts += ShareLook(self.started, laid.share).verdicts(
                "items[0].",
                node,
                laid.folder,
                laid.sharer,
                laid.recipient,
                self.status,
            )
        return verdicts


@dataclass(frozen=True)
class TheShareEntryIsRefused(
    Then[ASharedFolderAndACaller, list[EntityShareNode | Exception | None]]
):
    """한 자리가 권한 부족으로 거부된다."""

    @override
    def says(self) -> str:
        return Says(
            "그 항목은 권한 부족으로 거부됩니다",
            english="that entry is rejected for lack of permission",
        )

    @override
    def look(
        self,
        laid: ASharedFolderAndACaller,
        answered: Answered[list[EntityShareNode | Exception | None]],
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
        ]


__all__ = (
    "ASharedFolderAndACaller",
    "ASharedFolderAndSomeone",
    "Side",
    "TheShareNode",
    "TheShareEntryIsRefused",
    "TheSharesComeBack",
    "TheSearchedShares",
    "HOST",
)
