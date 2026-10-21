"""What a role scenario table says besides the call.

How the adapter is built lives in the tables' own conftest, and the rows a scenario
lays come from ``seeds``. This holds the type a role table is written against and the
checks more than one table shares.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.rbac.response import RoleNode
from ai.backend.common.dto.manager.v2.rbac.types import RoleSourceDTO, RoleStatusDTO
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.role import RoleData
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
from bai_scenario.seeds.rbac.role import TestSeedRole


@dataclass(frozen=True)
class RolesAndACaller:
    """역할 여럿과, 그것을 부를 사람. 역할은 부르는 사람이 속하지 않은 도메인에 있다."""

    roles: tuple[RoleData, ...]
    domain: DomainData
    caller: UserData

    @property
    def role(self) -> RoleData:
        """역할이 하나뿐인 행이 다루는 역할."""
        return self.roles[0]


@dataclass(frozen=True)
class RolesAndSomeone(Given[Any, RolesAndACaller]):
    """한 도메인에 둔 역할 여럿과, 다른 도메인에 사는 사람 한 명."""

    role: UserRole = UserRole.USER
    count: int = 1

    @override
    def describe(self) -> str:
        return f"한 도메인에 둔 커스텀 역할 {self.count}개와, 다른 도메인에 사는 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> RolesAndACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        target = await seeding.creating(TestSeedDomain(name_hint="target", description=WAS_HERE))
        roles = [
            await seeding.creating_from(TestSeedRole(lambda d: d.id, name_hint="role"), target)
            for _ in range(self.count)
        ]
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return RolesAndACaller(
            roles=tuple(seeding.made(one) for one in roles),
            domain=seeding.made(target),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class RoleLook:
    """미리 만든 역할의 노드가 어떤 값으로 와야 하는지. 이름은 미리 만든 것에서 읽는다."""

    started: datetime
    described: str | None = None
    deleted: bool = False

    def verdicts(
        self, prefix: str, node: RoleNode, laid: RoleData, domain: DomainData
    ) -> list[Verdict]:
        written = WrittenByThisRun(self.started)
        deleted_at: Verdict = (
            Held(f"{prefix}deleted_at", node.deleted_at, written)
            if self.deleted
            else Same(f"{prefix}deleted_at", node.deleted_at, None)
        )
        return [
            Same(f"{prefix}name", node.name, laid.name),
            Same(f"{prefix}description", node.description, self.described),
            Same(f"{prefix}source", node.source, RoleSourceDTO.CUSTOM),
            Same(f"{prefix}status", node.status, RoleStatusDTO.ACTIVE),
            Same(f"{prefix}auto_assign", node.auto_assign, False),
            Same(f"{prefix}scope_type", node.scope_type, DomainEntityType()),
            Held[UUID](
                f"{prefix}scope_id", node.scope_id, SameAs(domain.id, "역할을 둔 도메인의 id")
            ),
            Same(f"{prefix}role_preset_id", node.role_preset_id, None),
            Skipped(f"{prefix}id", "데이터베이스가 만든다"),
            Held[UUID](
                f"{prefix}entity_id", node.entity_id, SameAs(laid.id, "미리 만든 역할의 id")
            ),
            Held(f"{prefix}created_at", node.created_at, written),
            Held(f"{prefix}updated_at", node.updated_at, written),
            deleted_at,
        ]


@dataclass(frozen=True)
class NothingIsProcessed(Then[RolesAndACaller, PartialBulkPayload[RoleNode]]):
    """처리된 역할 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 역할 없이 대상이 모두 실패 목록에 온다"

    @override
    def look(
        self,
        laid: RolesAndACaller,
        answered: Answered[PartialBulkPayload[RoleNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.roles)),
        ]
        for i, (failure, role) in enumerate(zip(payload.failed, laid.roles, strict=False)):
            verdicts += [
                Held[UUID](f"failed[{i}].id", failure.id, SameAs(role.id, "대상 역할의 id")),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
