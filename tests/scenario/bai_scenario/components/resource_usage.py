"""What a resource usage scenario table says besides the call.

A usage bucket belongs to one resource group and one owner, and a read is either
unscoped (superadmin) or answered for by the resource group. A table needs that place
and the caller.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import Given, Says
from bai_scenario.components.domain import SomeoneOf
from bai_scenario.components.resource_allocation import lay_a_place
from bai_scenario.seeds.seeder import Laid


class Side(enum.Enum):
    """누가 부르는지."""

    SUPERADMIN = "superadmin"
    NOBODY = "nobody"


@dataclass(frozen=True)
class AUsageScopeAndACaller:
    """사용량 버킷을 훑을 자리와, 부르는 사람."""

    domain_name: str
    resource_group_name: str
    project_id: UUID
    user_id: UUID
    caller: UserData


@dataclass(frozen=True)
class AUsageScopeAndSomeone(Given[Any, AUsageScopeAndACaller]):
    """도메인, 리소스 그룹, 프로젝트, 사용자 하나와, 그중 부르는 사람."""

    who: Side = Side.SUPERADMIN

    @override
    def describe(self) -> str:
        who = "슈퍼관리자" if self.who is Side.SUPERADMIN else "아무 권한도 받지 않은 일반 사용자"
        who_en = (
            "one superadmin"
            if self.who is Side.SUPERADMIN
            else "one regular user holding no permission"
        )
        return Says(
            "사용량 버킷을 훑을 도메인, 리소스 그룹, 프로젝트, 사용자와, " + who,
            english=(
                "a domain, resource group, project and user to page usage buckets for, and "
                + who_en
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AUsageScopeAndACaller:
        place = await lay_a_place(seeding, slots=0)
        caller: Laid[UserData] = await seeding.within(
            SomeoneOf(
                place.domain,
                role=UserRole.SUPERADMIN if self.who is Side.SUPERADMIN else UserRole.USER,
            )
        )
        return AUsageScopeAndACaller(
            domain_name=seeding.made(place.domain).name,
            resource_group_name=seeding.made(place.group).name,
            project_id=seeding.made(place.project).id,
            user_id=seeding.made(place.owner).id,
            caller=seeding.made(caller),
        )


__all__ = ("AUsageScopeAndACaller", "AUsageScopeAndSomeone", "Side")
