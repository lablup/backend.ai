"""세션 생성."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.defs.session import SESSION_PRIORITY_DEFAULT
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.session.request import EnqueueSessionInput
from ai.backend.common.dto.manager.v2.session.response import EnqueueSessionPayload
from ai.backend.common.dto.manager.v2.session.types import CreateSessionTypeEnum
from ai.backend.common.types import IntrinsicSlotNames
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
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
from bai_scenario.components.domain import SomeoneOf, WrittenByThisRun
from bai_scenario.components.resource_allocation import lay_a_place
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.agent.agent import TestSeedAgent
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_group.resource_group import LinkToProject
from bai_scenario.seeds.resource_slot.agent_resource import TestSeedReportedSlot
from bai_scenario.seeds.resource_slot.slot_type import TestSeedSlotType
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest

type Enqueued = EnqueueSessionPayload

SESSION_NAME = "created-session"
ASKED_FOR: dict[str, Decimal] = {"cpu": Decimal(1), "mem": Decimal(2147483648)}
"""The slots the session asks for, above the image minimum of cpu 1 and mem 1.06g."""
CAPACITY: dict[str, Decimal] = {"cpu": Decimal(8), "mem": Decimal(34359738368)}
"""What the agent reports in each slot, more than the session asks for."""


@dataclass(frozen=True)
class SomeoneWhoMayCreateSessionsIn(TestSeedNest[Laid[UserData]]):
    """그 프로젝트에서 세션을 만들고 읽을 수 있는 사용자."""

    project: Laid[ProjectData]
    user: Laid[UserData]

    @override
    def kind(self) -> str:
        return Says(
            "그 프로젝트에서 세션을 만들고 읽을 수 있는 사용자 준비",
            english="Prepare a user who may create and read sessions in the project",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        role = seed.creating_from(
            TestSeedRole(lambda p: ProjectID(p.id), name_hint="session-owner"), self.project
        )
        seed.adding(
            TestSeedPermission(entity_type=SessionEntityType(), permission=Permission.CREATE), role
        )
        seed.adding(
            TestSeedPermission(entity_type=SessionEntityType(), permission=Permission.READ), role
        )
        seed.granting(role, self.user, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return self.user


@dataclass(frozen=True)
class LaidPlaceAndCaller:
    """세션을 만들 자리와, 그 세션을 요청할 사용자."""

    domain: DomainData
    project: ProjectData
    resource_group: ResourceGroupData
    image: ImageData
    caller: UserData
    access_key: str
    started: datetime


@dataclass(frozen=True)
class APlaceAndSomeone(Given[Any, LaidPlaceAndCaller]):
    """자원 그룹을 프로젝트에 연결해 둔 자리와, 세션을 만들 권한이 있는지 여부."""

    granted: bool = True

    @override
    def describe(self) -> str:
        laid_ko = "요구할 슬롯을 감당하는 에이전트가 있는 자원 그룹과 이미지"
        laid_en = "a resource group whose agent holds the slots a session asks for"
        if self.granted:
            return Says(
                f"{laid_ko}, 그리고 그 프로젝트에서 세션을 만들 수 있는 사용자 한 명",
                english=f"{laid_en}, and one user who may create sessions in that project",
            )
        return Says(
            f"{laid_ko}, 그리고 아무 권한도 받지 않은 사용자 한 명",
            english=f"{laid_en}, and one user holding no permission",
        )

    @override
    async def lay(self, seeding: Any) -> LaidPlaceAndCaller:
        place = await lay_a_place(seeding, slots=0)
        await seeding.linking(LinkToProject(), place.project, place.group)
        for intrinsic in IntrinsicSlotNames:
            await seeding.creating(TestSeedSlotType(intrinsic))
        agent = await seeding.creating_from(TestSeedAgent(), place.group)
        for slot_name, capacity in CAPACITY.items():
            await seeding.adding(
                TestSeedReportedSlot(
                    agent_id=agent.name,
                    slot_name=slot_name,
                    capacity=capacity,
                    used=Decimal(0),
                ),
                agent,
            )
        caller = await seeding.within(SomeoneOf(place.domain))
        if self.granted:
            await seeding.within(SomeoneWhoMayCreateSessionsIn(place.project, caller))
        return LaidPlaceAndCaller(
            domain=seeding.made(place.domain),
            project=seeding.made(place.project),
            resource_group=seeding.made(place.group),
            image=seeding.made(place.image),
            caller=seeding.made(caller),
            access_key=str(place.access_key),
            started=datetime.now(UTC),
        )


@dataclass(frozen=True)
class CreatingTheSession(When[LaidPlaceAndCaller, SessionAdapter, Enqueued]):
    @override
    def operation(self) -> str:
        return "enqueue"

    @override
    def describe(self, laid: LaidPlaceAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 그 프로젝트에 {SESSION_NAME} 세션을 만듭니다",
            english=f"{laid.caller.username} creates the session {SESSION_NAME} in that project",
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidPlaceAndCaller) -> Enqueued:
        with ActingAs(laid.caller):
            return await adapter.enqueue(
                EnqueueSessionInput(
                    session_name=SESSION_NAME,
                    session_type=CreateSessionTypeEnum.INTERACTIVE,
                    image_id=laid.image.id,
                    resource_entries=[
                        ResourceSlotEntryInput(resource_type=slot_name, quantity=str(amount))
                        for slot_name, amount in ASKED_FOR.items()
                    ],
                    resource_group_id=ResourceGroupID(laid.resource_group.id),
                    project_id=laid.project.id,
                    is_preemptible=False,
                ),
                user_id=laid.caller.id,
                user_role=laid.caller.role.value,
                access_key=laid.access_key,
                domain_name=laid.caller.domain_name,
                group_id=laid.project.id,
            )


@dataclass(frozen=True)
class ANonEmptyId(Condition[str | None]):
    """이 실행이 만든, 비어 있지 않은 값."""

    @override
    def says(self) -> str:
        return Says("이 실행이 만든 비어 있지 않은 값", english="a non-empty value this run made")

    @override
    def holds(self, got: str | None) -> bool:
        return bool(got)


@dataclass(frozen=True)
class TheAllocationAskingFor(Condition[dict[str, Any]]):
    """세션의 할당이 요구한 슬롯 모두를 그 양만큼 차 있고, 아직 실제로 잡힌 것은 없다."""

    asked: Mapping[str, Decimal]

    @override
    def says(self) -> str:
        asked = ", ".join(f"{name} {amount}" for name, amount in sorted(self.asked.items()))
        return Says(f"{asked} 만큼의 할당", english=f"the allocation of {asked}")

    @override
    def holds(self, got: dict[str, Any]) -> bool:
        def per_slot(info: dict[str, Any]) -> dict[str, Decimal]:
            return {
                str(entry["resource_type"]): Decimal(str(entry["quantity"]))
                for entry in info["entries"]
            }

        return (
            per_slot(got["requested"]) == self.asked
            and per_slot(got["used"]) == self.asked
            and not got["allocated"]["entries"]
        )


@dataclass(frozen=True)
class TheSessionIsCreated(Then[LaidPlaceAndCaller, Enqueued]):
    @override
    def says(self) -> str:
        return Says(
            "만들어진 세션 전체가 저장된 그대로 반환됩니다",
            english="the whole session that was created comes back as it was stored",
        )

    @override
    def look(self, laid: LaidPlaceAndCaller, answered: Answered[Enqueued]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        node = payload.session
        metadata = node.metadata
        resource = node.resource
        lifecycle = node.lifecycle
        runtime = node.runtime
        network = node.network
        return [
            Skipped("id", Says("데이터베이스가 생성합니다", english="the database generates it")),
            Held(
                "entity_id",
                node.entity_id,
                SameAs(node.id, Says("그 id", english="the id")),
            ),
            Held(
                "image_ids",
                node.image_ids,
                SameAs[list[UUID] | None](
                    [laid.image.id], Says("그 세션의 이미지", english="the image of the session")
                ),
            ),
            Same("domain_name", node.domain_name, laid.domain.name),
            Held(
                "user_id",
                node.user_id,
                SameAs[UUID | None](
                    laid.caller.id, Says("요청한 사용자의 id", english="the caller's id")
                ),
            ),
            Held(
                "project_id",
                node.project_id,
                SameAs(laid.project.id, Says("그 프로젝트의 id", english="the id of the project")),
            ),
            Held("metadata.creation_id", metadata.creation_id, ANonEmptyId()),
            Same("metadata.name", metadata.name, SESSION_NAME),
            Same("metadata.session_type", metadata.session_type, "interactive"),
            Same("metadata.access_key", metadata.access_key, laid.access_key),
            Same("metadata.cluster_mode", metadata.cluster_mode, "SINGLE_NODE"),
            Same("metadata.cluster_size", metadata.cluster_size, 1),
            Same("metadata.tier", metadata.tier, SESSION_PRIORITY_DEFAULT),
            Same("metadata.priority", metadata.priority, SESSION_PRIORITY_DEFAULT),
            Same("metadata.job_priority", metadata.job_priority, 0),
            Same("metadata.is_preemptible", metadata.is_preemptible, False),
            Same("metadata.tag", metadata.tag, None),
            Held(
                "resource.allocation",
                resource.allocation.model_dump(),
                TheAllocationAskingFor(ASKED_FOR),
            ),
            Same(
                "resource.resource_group_name",
                resource.resource_group_name,
                laid.resource_group.name,
            ),
            Same("resource.session_group_id", resource.session_group_id, None),
            Same("resource.designated_agent_ids", resource.designated_agent_ids, None),
            Same("lifecycle.status", lifecycle.status, "PENDING"),
            Same("lifecycle.result", lifecycle.result, "undefined"),
            Held(
                "lifecycle.created_at",
                lifecycle.created_at,
                WrittenByThisRun(laid.started),
            ),
            Same("lifecycle.terminated_at", lifecycle.terminated_at, None),
            Same("lifecycle.starts_at", lifecycle.starts_at, None),
            Same("lifecycle.requested_starts_at", lifecycle.requested_starts_at, None),
            Same("lifecycle.batch_timeout", lifecycle.batch_timeout, None),
            Same("runtime.environ", runtime.environ, None),
            Same("runtime.bootstrap_script", runtime.bootstrap_script, None),
            Same("runtime.startup_command", runtime.startup_command, None),
            Same("runtime.callback_url", runtime.callback_url, None),
            Same("network.use_host_network", network.use_host_network, False),
            Same("network.network_type", network.network_type, "volatile"),
            Same("network.network_id", network.network_id, None),
            Same("replica_id", node.replica_id, None),
        ]


@dataclass(frozen=True)
class CreatingASession(Scenario[TestSeedingSession, LaidPlaceAndCaller, SessionAdapter, Enqueued]):
    granted: bool = True

    @override
    def summary(self) -> str:
        who = "granted" if self.granted else "granted-nothing"
        return f"creating-a-session-{who}"

    @override
    def describe(self) -> str:
        if not self.granted:
            return Says(
                "아무 권한도 받지 않은 사용자가 프로젝트에 세션을 만들려 하면, 권한 부족으로 "
                "거부됩니다",
                english=(
                    "when a user granted nothing creates a session in a project, the call is "
                    "rejected for lack of permission"
                ),
            )
        return Says(
            "그 프로젝트에서 세션을 만들 수 있는 사용자가 세션을 만들면, 대기 상태의 세션 전체가 "
            "반환됩니다",
            english=(
                "when a user who may create sessions in the project creates one, the whole "
                "pending session comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidPlaceAndCaller]:
        return APlaceAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[LaidPlaceAndCaller, SessionAdapter, Enqueued]:
        return CreatingTheSession()

    @override
    def then(self) -> Then[LaidPlaceAndCaller, Enqueued]:
        if not self.granted:
            return TheCallIsRefused(NotEnoughPermission)
        return TheSessionIsCreated()


SCENARIOS: list[Scenario[Any, Any, Any, Any]] = [
    CreatingASession(),
    CreatingASession(granted=False),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_enqueueing(
    scenario: Scenario[Any, Any, Any, Any],
    adapter: SessionAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
