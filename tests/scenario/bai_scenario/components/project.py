"""What a project scenario table says besides the call.

How the adapter is built lives in the tables' own conftest, and the rows a scenario
lays come from ``seeds``. This holds the situations worth naming more than once.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.group.response import ProjectNode
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
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, Mentions, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy


@dataclass(frozen=True)
class ManyProjectsAndACaller:
    """건드릴 프로젝트 여럿과, 부르는 사람."""

    targets: tuple[ProjectData, ...]
    caller: UserData


@dataclass(frozen=True)
class ManyProjectsAndSomeone(Given[Any, ManyProjectsAndACaller]):
    """한 도메인 아래의 프로젝트 여럿과, 다른 도메인에 사는 사용자 한 명."""

    role: UserRole = UserRole.USER
    count: int = 2

    @override
    def describe(self) -> str:
        return f"한 도메인 아래의 프로젝트 {self.count}개와, 다른 도메인에 사는 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyProjectsAndACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        target = await seeding.creating(TestSeedDomain(name_hint="target", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        projects = [
            await seeding.creating_from_two(TestSeedProject(name_hint="team"), target, policy)
            for _ in range(self.count)
        ]
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return ManyProjectsAndACaller(
            targets=tuple(seeding.made(one) for one in projects),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ProjectLook:
    """미리 만든 프로젝트의 노드가 어떤 값으로 와야 하는지. 나머지 값은 미리 만든 것에서 읽는다."""

    started: datetime
    described: str | None = None
    active: bool = True

    def verdicts(self, prefix: str, node: ProjectNode, laid: ProjectData) -> list[Verdict]:
        written = WrittenByThisRun(self.started)
        described = self.described if self.described is not None else laid.description
        return [
            Same(f"{prefix}name", node.basic_info.name, laid.name),
            Same(f"{prefix}description", node.basic_info.description, described),
            Same(f"{prefix}integration_name", node.basic_info.integration_name, None),
            Same(f"{prefix}domain_name", node.organization.domain_name, laid.domain_name),
            Same(
                f"{prefix}resource_policy", node.organization.resource_policy, laid.resource_policy
            ),
            Same(f"{prefix}allowed_vfolder_hosts", node.storage.allowed_vfolder_hosts, []),
            Same(f"{prefix}is_active", node.lifecycle.is_active, self.active),
            Skipped(f"{prefix}id", "데이터베이스가 만든다"),
            Skipped(f"{prefix}type", "타입이 이미 값을 못박는다"),
            Held[UUID](
                f"{prefix}entity_id", node.entity_id, SameAs(laid.id, "미리 만든 프로젝트의 id")
            ),
            Held(f"{prefix}created_at", node.lifecycle.created_at, written),
            Held(f"{prefix}modified_at", node.lifecycle.modified_at, written),
        ]


@dataclass(frozen=True)
class NoProjectIsProcessed(Then[ManyProjectsAndACaller, PartialBulkPayload[ProjectNode]]):
    """처리된 프로젝트 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 프로젝트 없이 대상이 모두 실패 목록에 온다"

    @override
    def look(
        self,
        laid: ManyProjectsAndACaller,
        answered: Answered[PartialBulkPayload[ProjectNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.targets)),
        ]
        for i, (failure, project) in enumerate(zip(payload.failed, laid.targets, strict=False)):
            verdicts += [
                Held[UUID](f"failed[{i}].id", failure.id, SameAs(project.id, "대상 프로젝트의 id")),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
