"""What a service catalog scenario table says besides the call.

A service is registered in no scope, so a table lays no place for it: only the caller and
the services the search reads. A service is laid healthy unless a table asks for the status
filter, which needs one of every status side by side.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.service_catalog.response import (
    AdminSearchServiceCatalogsPayload,
    ServiceCatalogNode,
)
from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.data.service_catalog.types import ServiceCatalogEndpointData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.auth import InsufficientPrivilege
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
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.system import lay_a_caller, role_named
from bai_scenario.seeds.service_catalog.service import (
    STARTED_UP,
    STATUS_NAMES,
    VERSION,
    SeedEndpointOf,
    SeedService,
    SeedServiceInStatus,
)

GROUP = "manager"
"""The group the services a table lays belong to."""

OTHER_GROUP = "agent"
"""The group a service laid beside them belongs to, for a filter to tell apart."""


@dataclass(frozen=True)
class ALaidService:
    """심은 서비스 하나. id는 쓰기가 답한 것이고, 나머지는 seed가 정한 값이다."""

    id: ServiceCatalogID
    service_group: str
    instance_id: str
    status: ServiceCatalogStatus
    endpoints: tuple[ServiceCatalogEndpointData, ...]


@dataclass(frozen=True)
class ManyServicesAndACaller:
    """검색할 서비스 여럿과, 검색을 부를 사용자. ``named``는 그중 필터로 골라낼 하나다."""

    laid: tuple[ALaidService, ...]
    named: ALaidService
    caller: UserData


@dataclass(frozen=True)
class ManyServicesAndSomeone(Given[Any, ManyServicesAndACaller]):
    """같은 그룹의 서비스 여럿과 사용자 한 명. 첫 서비스만 엔드포인트 하나를 갖는다."""

    role: UserRole = UserRole.USER
    besides: int = 1

    @override
    def describe(self) -> str:
        return f"서비스 {self.besides + 1}개와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyServicesAndACaller:
        wanted = await seeding.creating(SeedService(service_group=GROUP, name_hint="wanted"))
        endpoint = await seeding.adding(SeedEndpointOf(), wanted)
        others = [
            await seeding.creating(SeedService(service_group=GROUP, name_hint="other"))
            for _ in range(self.besides)
        ]
        caller = await lay_a_caller(seeding, self.role)
        first = ALaidService(
            seeding.made(wanted),
            GROUP,
            wanted.name,
            ServiceCatalogStatus.HEALTHY,
            (seeding.made(endpoint),),
        )
        rest = [
            ALaidService(seeding.made(one), GROUP, one.name, ServiceCatalogStatus.HEALTHY, ())
            for one in others
        ]
        return ManyServicesAndACaller(laid=(first, *rest), named=first, caller=seeding.made(caller))


@dataclass(frozen=True)
class ServicesOfTwoGroupsAndSomeone(Given[Any, ManyServicesAndACaller]):
    """그룹이 다른 서비스 둘과 사용자 한 명. ``named``는 첫 그룹의 것이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"그룹이 다른 서비스 둘과, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyServicesAndACaller:
        wanted = await seeding.creating(SeedService(service_group=GROUP, name_hint="wanted"))
        other = await seeding.creating(SeedService(service_group=OTHER_GROUP, name_hint="other"))
        caller = await lay_a_caller(seeding, self.role)
        first = ALaidService(
            seeding.made(wanted), GROUP, wanted.name, ServiceCatalogStatus.HEALTHY, ()
        )
        second = ALaidService(
            seeding.made(other), OTHER_GROUP, other.name, ServiceCatalogStatus.HEALTHY, ()
        )
        return ManyServicesAndACaller(
            laid=(first, second), named=first, caller=seeding.made(caller)
        )


@dataclass(frozen=True)
class ServicesOfEveryStatusAndSomeone(Given[Any, ManyServicesAndACaller]):
    """상태마다 서비스 하나씩과 사용자 한 명. ``named``는 정상 상태의 것이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        listed = "·".join(STATUS_NAMES[one] for one in ServiceCatalogStatus)
        return f"{listed} 상태의 서비스 하나씩과, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyServicesAndACaller:
        healthy = await seeding.creating(SeedService(service_group=GROUP, name_hint="healthy"))
        others = [
            (
                status,
                await seeding.creating(
                    SeedServiceInStatus(service_group=GROUP, status=status, name_hint=status.value)
                ),
            )
            for status in ServiceCatalogStatus
            if status is not ServiceCatalogStatus.HEALTHY
        ]
        caller = await lay_a_caller(seeding, self.role)
        first = ALaidService(
            seeding.made(healthy), GROUP, healthy.name, ServiceCatalogStatus.HEALTHY, ()
        )
        rest = [
            ALaidService(seeding.made(one), GROUP, one.name, status, ()) for status, one in others
        ]
        return ManyServicesAndACaller(laid=(first, *rest), named=first, caller=seeding.made(caller))


def service_verdicts(
    at: str, node: ServiceCatalogNode, *, laid: ALaidService, written: WrittenByThisRun
) -> list[Verdict]:
    """Every place of one service node, prefixed for a node inside a list."""
    seen: list[Verdict] = [
        Held[UUID](f"{at}id", node.id, SameAs[UUID](laid.id, "심은 서비스")),
        Same(f"{at}service_group", node.service_group, laid.service_group),
        Same(f"{at}instance_id", node.instance_id, laid.instance_id),
        Same(f"{at}display_name", node.display_name, laid.instance_id),
        Same(f"{at}version", node.version, VERSION),
        Same(f"{at}labels", node.labels, {}),
        Same(f"{at}status", node.status, laid.status),
        Same(f"{at}startup_time", node.startup_time, STARTED_UP),
        Held(f"{at}registered_at", node.registered_at, written),
        Held(f"{at}last_heartbeat", node.last_heartbeat, written),
        Same(f"{at}config_hash", node.config_hash, ""),
        Same(f"{at}len(endpoints)", len(node.endpoints), len(laid.endpoints)),
    ]
    for j, (got, expected) in enumerate(zip(node.endpoints, laid.endpoints, strict=False)):
        seen.extend([
            Skipped(f"{at}endpoints[{j}].id", "데이터베이스가 만든다"),
            Same(f"{at}endpoints[{j}].role", got.role, expected.role),
            Same(f"{at}endpoints[{j}].scope", got.scope, expected.scope),
            Same(f"{at}endpoints[{j}].address", got.address, expected.address),
            Same(f"{at}endpoints[{j}].port", got.port, expected.port),
            Same(f"{at}endpoints[{j}].protocol", got.protocol, expected.protocol),
            Same(f"{at}endpoints[{j}].metadata", got.metadata, expected.metadata),
        ])
    return seen


@dataclass(frozen=True)
class EveryLaidServiceComesWhole(Then[ManyServicesAndACaller, AdminSearchServiceCatalogsPayload]):
    """심은 서비스가 모두 집계되고, 각각이 엔드포인트까지 통째로 온다. 인스턴스 id 순으로 본다."""

    started: datetime

    @override
    def says(self) -> str:
        return "심은 서비스가 모두, 엔드포인트와 함께 통째로 집계된다"

    @override
    def look(
        self, laid: ManyServicesAndACaller, answered: Answered[AdminSearchServiceCatalogsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        written = WrittenByThisRun(self.started)
        got = sorted(payload.items, key=lambda one: one.instance_id)
        expected = sorted(laid.laid, key=lambda one: one.instance_id)
        seen: list[Verdict] = [
            Same(
                "items.instance_id",
                [one.instance_id for one in got],
                [one.instance_id for one in expected],
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        for i, (node, one) in enumerate(zip(got, expected, strict=False)):
            seen.extend(service_verdicts(f"items[{i}].", node, laid=one, written=written))
        return seen


@dataclass(frozen=True)
class OnlyTheServicesOfStatuses(Then[ManyServicesAndACaller, AdminSearchServiceCatalogsPayload]):
    """심은 서비스 중 이 상태들의 것만, 그리고 그것들 모두가 반환된다."""

    statuses: tuple[ServiceCatalogStatus, ...]

    @override
    def says(self) -> str:
        listed = "·".join(STATUS_NAMES[one] for one in self.statuses)
        return f"{listed} 상태의 서비스만 반환된다"

    @override
    def look(
        self, laid: ManyServicesAndACaller, answered: Answered[AdminSearchServiceCatalogsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        expected = [one for one in laid.laid if one.status in self.statuses]
        return [
            Held(
                "items.id",
                sorted(str(one.id) for one in payload.items),
                SameAs(sorted(str(one.id) for one in expected), "그 상태로 심은 서비스"),
            ),
            Same(
                "items.instance_id",
                sorted(one.instance_id for one in payload.items),
                sorted(one.instance_id for one in expected),
            ),
            Same(
                "items.status",
                sorted(one.status for one in payload.items),
                sorted(one.status for one in expected),
            ),
            Same("total_count", payload.total_count, len(expected)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedGroupIsLeft(Then[ManyServicesAndACaller, AdminSearchServiceCatalogsPayload]):
    """골라낸 그룹의 서비스만 남는다."""

    @override
    def says(self) -> str:
        return "골라낸 그룹의 서비스 하나만 남는다"

    @override
    def look(
        self, laid: ManyServicesAndACaller, answered: Answered[AdminSearchServiceCatalogsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Held(
                "items.id",
                [str(one.id) for one in payload.items],
                SameAs([str(laid.named.id)], "골라낸 서비스"),
            ),
            Same(
                "items.service_group",
                [one.service_group for one in payload.items],
                [laid.named.service_group],
            ),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheFirstPageOfServices(Then[ManyServicesAndACaller, AdminSearchServiceCatalogsPayload]):
    """크기를 지정하지 않은 첫 페이지. 기본 크기만큼 반환되고 다음 페이지가 있다고 응답한다."""

    size: int

    @override
    def says(self) -> str:
        return "기본 크기의 첫 페이지가 반환된다"

    @override
    def look(
        self, laid: ManyServicesAndACaller, answered: Answered[AdminSearchServiceCatalogsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Same("len(items)", len(payload.items), self.size),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
