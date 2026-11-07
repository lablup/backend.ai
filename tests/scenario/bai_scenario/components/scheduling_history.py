"""What a scheduling history scenario table says besides the call.

A history row belongs to the session, kernel, deployment, replica or replica group it
records a transition of. A table needs those rows, one history row for each, and the
caller the read is answered for.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.deployment.types import (
    DeploymentHistoryData,
    DeploymentInfo,
    ReplicaGroupData,
    ReplicaGroupHistoryData,
    RouteHistoryData,
)
from ai.backend.manager.data.kernel.types import KernelInfo, KernelSchedulingHistoryData
from ai.backend.manager.data.model_serving.types import RoutingData
from ai.backend.manager.data.session.types import (
    SessionEntityData,
    SessionSchedulingHistoryData,
)
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
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import SomeoneOf, WrittenByThisRun
from bai_scenario.components.resource_allocation import LaidPlace, lay_a_place
from bai_scenario.seeds.deployment.deployment import TestSeedDeployment
from bai_scenario.seeds.scheduling_history.history import (
    TestSeedDeploymentHistory,
    TestSeedKernelHistory,
    TestSeedReplicaGroupHistory,
    TestSeedReplicaOf,
    TestSeedRouteHistory,
    TestSeedSessionHistory,
)
from bai_scenario.seeds.session.kernel import TestSeedKernelOf, TestSeedMainKernelGroupOf
from bai_scenario.seeds.session.session import TestSeedSession
from bai_scenario.seeds.session_group.session_group import (
    TestSeedDeploymentSessionGroup,
    TestSeedPrimaryReplicaGroupOf,
)

SESSION = "session"
KERNEL = "kernel"
DEPLOYMENT = "deployment"
ROUTE = "route"
REPLICA_GROUP = "replica_group"


class Side(enum.Enum):
    """누가 부르는지."""

    SUPERADMIN = "superadmin"
    NOBODY = "nobody"


@dataclass(frozen=True)
class HistoriesAndACaller:
    """이력 다섯 줄과, 그 줄들이 딛는 행들, 그리고 부르는 사람."""

    session: SessionEntityData
    kernel: KernelInfo
    deployment: DeploymentInfo
    replica: RoutingData
    replica_group: ReplicaGroupData
    session_history: SessionSchedulingHistoryData
    kernel_history: KernelSchedulingHistoryData
    deployment_history: DeploymentHistoryData
    route_history: RouteHistoryData
    replica_group_history: ReplicaGroupHistoryData
    caller: UserData

    def history_id(self, kind: str) -> UUID:
        match kind:
            case "session":
                return self.session_history.id
            case "kernel":
                return self.kernel_history.id
            case "deployment":
                return self.deployment_history.id
            case "route":
                return self.route_history.id
            case _:
                return self.replica_group_history.id


def _who(side: Side) -> str:
    match side:
        case Side.SUPERADMIN:
            return "슈퍼관리자"
        case Side.NOBODY:
            return "아무 권한도 받지 않은 일반 사용자"


def _who_en(side: Side) -> str:
    match side:
        case Side.SUPERADMIN:
            return "one superadmin"
        case Side.NOBODY:
            return "one regular user holding no permission"


@dataclass(frozen=True)
class HistoriesAndSomeone(Given[Any, HistoriesAndACaller]):
    """세션 하나와 그 커널, 배포 하나와 그 복제본 그룹과 복제본, 그리고 이력 다섯 줄.

    이력 한 줄씩이 세션, 커널, 배포, 라우트, 복제본 그룹에 붙어 있다. ``who``가 부르는
    사람이다. ``outside`` 면 같은 다섯 가지를 한 벌 더 세워, 범위를 대고 훑을 때 걸러지는지
    볼 수 있게 한다.
    """

    who: Side = Side.SUPERADMIN
    outside: bool = False

    @override
    def describe(self) -> str:
        if self.outside:
            return Says(
                "스케줄링 이력이 붙은 세션, 커널, 배포, 라우트, 복제본 그룹이 한 벌, 범위 밖에 "
                f"같은 것이 한 벌 더 있고, {_who(self.who)}",
                english=(
                    "one set of a session, kernel, deployment, route and replica group carrying "
                    "a scheduling history row, one more set of each outside the scope, and "
                    f"{_who_en(self.who)}"
                ),
            )
        return Says(
            "스케줄링 이력이 하나씩 붙은 세션, 커널, 배포, 라우트, 복제본 그룹과, "
            f"{_who(self.who)}",
            english=(
                "one session, kernel, deployment, route and replica group each carrying one "
                f"scheduling history row, and {_who_en(self.who)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> HistoriesAndACaller:
        place = await lay_a_place(seeding, slots=0)
        session = await seeding.creating_from_three(
            TestSeedSession(access_key=place.access_key),
            place.project,
            place.owner,
            place.group,
        )
        kernel_group = await seeding.adding(
            TestSeedMainKernelGroupOf(image=seeding.made(place.image), slots=()), session
        )
        kernel = await seeding.adding_with_nested(
            TestSeedKernelOf(
                session=seeding.made(session),
                group=seeding.made(kernel_group),
                image=seeding.made(place.image),
                slots=(),
            ),
            session,
        )
        deployment = await seeding.creating_from_three(
            TestSeedDeployment(), place.project, place.group, place.owner
        )
        deployment_value = seeding.made(deployment)
        session_group = await seeding.creating_from(TestSeedDeploymentSessionGroup(), deployment)
        replica_group = await seeding.adding(
            TestSeedPrimaryReplicaGroupOf(SessionGroupID(seeding.made(session_group).id)),
            deployment,
        )
        replica = await seeding.adding(
            TestSeedReplicaOf(
                replica_group_id=ReplicaGroupID(seeding.made(replica_group).id),
                session_owner_id=deployment_value.metadata.session_owner,
                domain_name=deployment_value.metadata.domain,
                project_id=deployment_value.metadata.project,
            ),
            deployment,
        )
        session_history = await seeding.adding(TestSeedSessionHistory(), session)
        kernel_history = await seeding.adding(
            TestSeedKernelHistory(kernel_id=seeding.made(kernel).id), session
        )
        deployment_history = await seeding.adding(TestSeedDeploymentHistory(), deployment)
        route_history = await seeding.adding(
            TestSeedRouteHistory(route_id=ReplicaID(seeding.made(replica).id)), deployment
        )
        replica_group_history = await seeding.adding(
            TestSeedReplicaGroupHistory(
                replica_group_id=ReplicaGroupID(seeding.made(replica_group).id)
            ),
            deployment,
        )
        if self.outside:
            await self._lay_outside(seeding, place)
        caller = await seeding.within(
            SomeoneOf(
                place.domain,
                role=UserRole.SUPERADMIN if self.who is Side.SUPERADMIN else UserRole.USER,
            )
        )
        return HistoriesAndACaller(
            session=seeding.made(session),
            kernel=seeding.made(kernel),
            deployment=deployment_value,
            replica=seeding.made(replica),
            replica_group=seeding.made(replica_group),
            session_history=seeding.made(session_history),
            kernel_history=seeding.made(kernel_history),
            deployment_history=seeding.made(deployment_history),
            route_history=seeding.made(route_history),
            replica_group_history=seeding.made(replica_group_history),
            caller=seeding.made(caller),
        )

    async def _lay_outside(self, seeding: Any, place: LaidPlace) -> None:
        """같은 다섯 가지를 한 벌 더 세운다. 범위를 대고 훑으면 이 벌은 걸러져야 한다."""
        session = await seeding.creating_from_three(
            TestSeedSession(access_key=place.access_key, name_hint="other-session"),
            place.project,
            place.owner,
            place.group,
        )
        kernel_group = await seeding.adding(
            TestSeedMainKernelGroupOf(image=seeding.made(place.image), slots=()), session
        )
        kernel = await seeding.adding_with_nested(
            TestSeedKernelOf(
                session=seeding.made(session),
                group=seeding.made(kernel_group),
                image=seeding.made(place.image),
                slots=(),
            ),
            session,
        )
        await seeding.adding(TestSeedSessionHistory(), session)
        await seeding.adding(TestSeedKernelHistory(kernel_id=seeding.made(kernel).id), session)
        deployment = await seeding.creating_from_three(
            TestSeedDeployment(name_hint="other-deployment"),
            place.project,
            place.group,
            place.owner,
        )
        deployment_value = seeding.made(deployment)
        await seeding.adding(TestSeedDeploymentHistory(), deployment)
        session_group = await seeding.creating_from(TestSeedDeploymentSessionGroup(), deployment)
        replica_group = await seeding.adding(
            TestSeedPrimaryReplicaGroupOf(SessionGroupID(seeding.made(session_group).id)),
            deployment,
        )
        await seeding.adding(
            TestSeedReplicaGroupHistory(
                replica_group_id=ReplicaGroupID(seeding.made(replica_group).id)
            ),
            deployment,
        )
        replica = await seeding.adding(
            TestSeedReplicaOf(
                replica_group_id=ReplicaGroupID(seeding.made(replica_group).id),
                session_owner_id=deployment_value.metadata.session_owner,
                domain_name=deployment_value.metadata.domain,
                project_id=deployment_value.metadata.project,
            ),
            deployment,
        )
        await seeding.adding(
            TestSeedRouteHistory(route_id=ReplicaID(seeding.made(replica).id)), deployment
        )


HISTORY_ID = Says("미리 만든 이력의 id", english="the id of the history laid in advance")
SESSION_ID = Says("미리 만든 세션의 id", english="the id of the session laid in advance")
KERNEL_ID = Says("미리 만든 커널의 id", english="the id of the kernel laid in advance")
DEPLOYMENT_ID = Says("미리 만든 배포의 id", english="the id of the deployment laid in advance")
REPLICA_ID = Says("미리 만든 복제본의 id", english="the id of the replica laid in advance")
"""미리 만든 행의 id 를 가리키는 말."""


def _verdicts(
    kind: str, laid: HistoriesAndACaller, prefix: str, node: Any, started: datetime
) -> list[Verdict]:
    written = WrittenByThisRun(started)
    tail: list[Verdict] = [
        Same(f"{prefix}result", node.result, "SUCCESS"),
        Same(f"{prefix}error_code", node.error_code, None),
        Same(f"{prefix}message", node.message, _history_of(kind, laid).message),
        Same(f"{prefix}attempts", node.attempts, 1),
        Held(f"{prefix}created_at", node.created_at, written),
        Held(f"{prefix}updated_at", node.updated_at, written),
    ]

    def with_sub_steps() -> list[Verdict]:
        # The kernel history table carries no sub-steps column.
        return [*tail[:3], Same(f"{prefix}sub_steps", node.sub_steps, []), *tail[3:]]

    match kind:
        case "session":
            return [
                Held[UUID](f"{prefix}id", node.id, SameAs(laid.session_history.id, HISTORY_ID)),
                Held[UUID](
                    f"{prefix}field_id",
                    node.field_id,
                    SameAs(laid.session_history.id, HISTORY_ID),
                ),
                Held[UUID](
                    f"{prefix}session_id",
                    node.session_id,
                    SameAs(laid.session.id, SESSION_ID),
                ),
                Same(f"{prefix}phase", node.phase, laid.session_history.phase),
                Same(f"{prefix}from_status", node.from_status, "PENDING"),
                Same(f"{prefix}to_status", node.to_status, "SCHEDULED"),
                *with_sub_steps(),
            ]
        case "kernel":
            return [
                Held[UUID](f"{prefix}id", node.id, SameAs(laid.kernel_history.id, HISTORY_ID)),
                Held[UUID](
                    f"{prefix}field_id",
                    node.field_id,
                    SameAs(laid.kernel_history.id, HISTORY_ID),
                ),
                Held[UUID](f"{prefix}kernel_id", node.kernel_id, SameAs(laid.kernel.id, KERNEL_ID)),
                Held[UUID](
                    f"{prefix}session_id",
                    node.session_id,
                    SameAs(laid.session.id, SESSION_ID),
                ),
                Same(f"{prefix}phase", node.phase, laid.kernel_history.phase),
                Same(f"{prefix}from_status", node.from_status, "PREPARING"),
                Same(f"{prefix}to_status", node.to_status, "PULLING"),
                *tail,
            ]
        case "deployment" | "replica_group":
            history = _history_of(kind, laid)
            return [
                Held[UUID](f"{prefix}id", node.id, SameAs(history.id, HISTORY_ID)),
                Held[UUID](f"{prefix}field_id", node.field_id, SameAs(history.id, HISTORY_ID)),
                Held[UUID](
                    f"{prefix}deployment_id",
                    node.deployment_id,
                    SameAs(laid.deployment.id, DEPLOYMENT_ID),
                ),
                Same(f"{prefix}category", node.category, "lifecycle"),
                Same(f"{prefix}phase", node.phase, history.phase),
                Same(f"{prefix}from_status", node.from_status, None),
                Same(f"{prefix}to_status", node.to_status, None),
                *with_sub_steps(),
            ]
        case _:
            return [
                Held[UUID](f"{prefix}id", node.id, SameAs(laid.route_history.id, HISTORY_ID)),
                Held[UUID](
                    f"{prefix}field_id",
                    node.field_id,
                    SameAs(laid.route_history.id, HISTORY_ID),
                ),
                Held[UUID](f"{prefix}route_id", node.route_id, SameAs(laid.replica.id, REPLICA_ID)),
                Held[UUID](
                    f"{prefix}deployment_id",
                    node.deployment_id,
                    SameAs(laid.deployment.id, DEPLOYMENT_ID),
                ),
                Same(f"{prefix}category", node.category, "lifecycle"),
                Same(f"{prefix}phase", node.phase, laid.route_history.phase),
                Same(f"{prefix}from_status", node.from_status, "provisioning"),
                Same(f"{prefix}to_status", node.to_status, "running"),
                Same(f"{prefix}from_sub_status", node.from_sub_status, "pending"),
                Same(f"{prefix}to_sub_status", node.to_sub_status, "warming_up"),
                *with_sub_steps(),
            ]


type AnyHistory = (
    SessionSchedulingHistoryData
    | KernelSchedulingHistoryData
    | DeploymentHistoryData
    | ReplicaGroupHistoryData
    | RouteHistoryData
)


def _history_of(kind: str, laid: HistoriesAndACaller) -> AnyHistory:
    match kind:
        case "session":
            return laid.session_history
        case "kernel":
            return laid.kernel_history
        case "deployment":
            return laid.deployment_history
        case "route":
            return laid.route_history
        case _:
            return laid.replica_group_history


@dataclass(frozen=True)
class TheHistoryComesBack(Then[HistoriesAndACaller, list[Any]]):
    """그 이력이 노드로 온다. 없는 id 자리는 빈 값이다."""

    kind: str
    started: datetime
    missing: bool = False

    @override
    def says(self) -> str:
        if self.missing:
            return Says(
                "미리 만든 이력은 노드로, 없는 id 자리는 빈 값으로 옵니다",
                english=(
                    "the history laid in advance comes back as a node and the unknown id "
                    "entry as an empty value"
                ),
            )
        return Says(
            "미리 만든 이력이 노드로 옵니다",
            english="the history laid in advance comes back as a node",
        )

    @override
    def look(self, laid: HistoriesAndACaller, answered: Answered[list[Any]]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        expected = 1 + (1 if self.missing else 0)
        verdicts: list[Verdict] = [Same("length", len(loaded), expected)]
        if len(loaded) != expected:
            return verdicts
        verdicts += _verdicts(self.kind, laid, "[0].", loaded[0], self.started)
        if self.missing:
            verdicts.append(Same("[1]", loaded[1], None))
        return verdicts


@dataclass(frozen=True)
class TheHistoryLoadIsRefused(Then[HistoriesAndACaller, list[Any]]):
    """한 자리가 권한 부족으로 거부된다."""

    @override
    def says(self) -> str:
        return Says(
            "그 항목은 권한 부족으로 거부됩니다",
            english="that entry is rejected for lack of permission",
        )

    @override
    def look(self, laid: HistoriesAndACaller, answered: Answered[list[Any]]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
        ]


@dataclass(frozen=True)
class TheHistoriesAreFound(Then[HistoriesAndACaller, Any]):
    """그 이력 하나가 한 페이지로 온다."""

    kind: str
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 만든 이력 하나가 한 페이지로 옵니다",
            english="the one history laid in advance comes back as one page",
        )

    @override
    def look(self, laid: HistoriesAndACaller, answered: Answered[Any]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("items count", len(page.items), 1),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
        if page.items:
            verdicts += _verdicts(self.kind, laid, "items[0].", page.items[0], self.started)
        return verdicts


__all__ = (
    "DEPLOYMENT",
    "KERNEL",
    "REPLICA_GROUP",
    "ROUTE",
    "SESSION",
    "HistoriesAndACaller",
    "HistoriesAndSomeone",
    "Side",
    "TheHistoriesAreFound",
    "TheHistoryComesBack",
    "TheHistoryLoadIsRefused",
)
