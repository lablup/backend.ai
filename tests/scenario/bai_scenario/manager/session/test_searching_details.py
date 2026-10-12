"""저장된 스케줄링 조건을 포함한 세션 조회 응답 전체."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
from ai.backend.common.dto.manager.v2.session.response import AdminSearchSessionsPayload
from ai.backend.common.types import AgentId, SessionTypes
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.session.options import KernelExecutionSpec, KernelResourceConfig
from ai.backend.manager.data.session.spec import KernelSpec
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.data.session_group.types import SessionGroupData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.session.creators import SessionCreator
from ai.backend.manager.models.session_group.creators import SessionGroupCreator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.resource_allocation import Granted, lay_a_caller_of, lay_a_place
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.agent.agent import TestSeedAgent
from bai_scenario.seeds.seeder import Naming, TestSeedRowFromTwo
from bai_scenario.seeds.session.session import TestSeedSession


@dataclass(frozen=True)
class TestSeedSessionGroup(TestSeedRowFromTwo[ProjectData, UserData, SessionGroupData]):
    @override
    def kind(self) -> str:
        return "세션 그룹"

    @override
    def detail(self) -> str:
        return "가능하면 세션들을 서로 다른 에이전트에 배치한다"

    @override
    def name(self, naming: Naming) -> str:
        return naming("session-group")

    @override
    def seed(self, name: str, first: ProjectData, second: UserData) -> SessionGroupCreator:
        return SessionGroupCreator.for_replica_group(
            domain_name=first.domain_name,
            project_id=ProjectID(first.id),
            owner_user_id=UserID(second.id),
        )


@dataclass(frozen=True, kw_only=True)
class TestSeedSessionWithSchedulingConditions(TestSeedSession):
    image_id: ImageID
    session_group_id: SessionGroupID
    designated_agents: tuple[AgentId, ...]

    @override
    def detail(self) -> str:
        return "세션 그룹, designated_agent_ids 둘, requested_starts_at을 지정한 대기 세션"

    @override
    def seed(
        self, name: str, first: ProjectData, second: UserData, third: ResourceGroupData
    ) -> SessionCreator:
        creator = super().seed(name, first, second, third)
        resource_spec = creator.spec.resource_spec
        kernel = KernelSpec(
            cluster_role="main",
            cluster_idx=1,
            cluster_hostname="main1",
            local_rank=0,
            execution_spec=KernelExecutionSpec(
                resource_input=KernelResourceConfig(image_id=self.image_id),
                starts_at=datetime(2030, 1, 2, 3, 4, tzinfo=UTC),
            ),
        )
        scheduling_target = resource_spec.options.scheduling_target.model_copy(
            update={"designated_agents": list(self.designated_agents)}
        )
        options = resource_spec.options.model_copy(update={"scheduling_target": scheduling_target})
        classification = resource_spec.classification.model_copy(
            update={"session_type": SessionTypes.BATCH}
        )
        resource_spec = resource_spec.model_copy(
            update={
                "classification": classification,
                "kernel_specs": (kernel,),
                "options": options,
            }
        )
        scope = creator.spec.scope.model_copy(update={"session_group_id": self.session_group_id})
        spec = creator.spec.model_copy(update={"scope": scope, "resource_spec": resource_spec})
        return replace(creator, spec=spec)


@dataclass(frozen=True)
class ASessionAndACaller:
    session: SessionEntityData
    caller: UserData


@dataclass(frozen=True)
class ASessionToRead(Given[TestSeedingSession, ASessionAndACaller]):
    configured: bool

    @override
    def describe(self) -> str:
        detail = "세 값이 지정된" if self.configured else "세 값이 미설정인"
        return f"세션 그룹, designated_agent_ids, requested_starts_at의 {detail} 세션과 슈퍼관리자"

    @override
    async def lay(self, seeding: TestSeedingSession) -> ASessionAndACaller:
        place = await lay_a_place(seeding, slots=0)
        session_seed: TestSeedSession = TestSeedSession(access_key=place.access_key)
        if self.configured:
            group = await seeding.creating_from_two(
                TestSeedSessionGroup(), place.project, place.owner
            )
            first_agent = await seeding.creating_from(TestSeedAgent(), place.group)
            second_agent = await seeding.creating_from(TestSeedAgent(), place.group)
            session_seed = TestSeedSessionWithSchedulingConditions(
                access_key=place.access_key,
                image_id=ImageID(seeding.made(place.image).id),
                session_group_id=seeding.made(group).id,
                designated_agents=(AgentId(first_agent.name), AgentId(second_agent.name)),
            )
        session = await seeding.creating_from_three(
            session_seed, place.project, place.owner, place.group
        )
        caller = await lay_a_caller_of(
            seeding, place, role=UserRole.SUPERADMIN, granted=Granted.NOTHING
        )
        return ASessionAndACaller(session=seeding.made(session), caller=seeding.made(caller))


@dataclass(frozen=True)
class SearchingSessions(When[ASessionAndACaller, SessionAdapter, AdminSearchSessionsPayload]):
    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ASessionAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(
        self, adapter: SessionAdapter, laid: ASessionAndACaller
    ) -> AdminSearchSessionsPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchSessionsInput())


@dataclass(frozen=True)
class TheWholeSessionIsReturned(Then[ASessionAndACaller, AdminSearchSessionsPayload]):
    @override
    def says(self) -> str:
        return "스케줄링 조건을 포함한 세션 정보 전체가 저장된 그대로 반환된다"

    @override
    def look(
        self, laid: ASessionAndACaller, answered: Answered[AdminSearchSessionsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        session = laid.session
        expected = {
            "id": session.id,
            "entity_id": session.id,
            "image_ids": [],
            "domain_name": session.domain_name,
            "user_id": session.user_uuid,
            "project_id": session.group_id,
            "metadata": {
                "creation_id": session.creation_id,
                "name": session.name,
                "session_type": session.session_type.value,
                "access_key": session.access_key,
                "cluster_mode": "SINGLE_NODE",
                "cluster_size": 1,
                "tier": 0,
                "priority": 0,
                "job_priority": 0,
                "is_preemptible": False,
                "tag": None,
            },
            "resource": {
                "allocation": {
                    "requested": {"entries": []},
                    "used": {"entries": []},
                    "allocated": {"entries": []},
                },
                "resource_group_name": session.resource_group_name,
                "session_group_id": session.session_group_id,
                "designated_agent_ids": session.designated_agent_ids,
            },
            "lifecycle": {
                "status": "PENDING",
                "result": "undefined",
                "created_at": session.created_at,
                "terminated_at": None,
                "starts_at": None,
                "requested_starts_at": session.requested_starts_at,
                "batch_timeout": None,
            },
            "runtime": {
                "environ": None,
                "bootstrap_script": None,
                "startup_command": None,
                "callback_url": None,
            },
            "network": {
                "use_host_network": False,
                "network_type": "volatile",
                "network_id": None,
            },
            "replica_id": None,
        }
        return [
            Held(
                "items",
                [node.model_dump() for node in page.items],
                SameAs([expected], "저장된 세션의 전체 정보"),
            ),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class SessionSchedulingConditionsArePreserved(
    Scenario[TestSeedingSession, ASessionAndACaller, SessionAdapter, AdminSearchSessionsPayload]
):
    configured: bool

    @override
    def summary(self) -> str:
        suffix = "configured" if self.configured else "unset"
        return f"session-scheduling-conditions-are-preserved-when-{suffix}"

    @override
    def describe(self) -> str:
        detail = "지정된" if self.configured else "미설정인"
        return f"슈퍼관리자가 {detail} 세션 스케줄링 조건을 읽으면 기존 세션 정보와 함께 유지된다"

    @override
    def given(self) -> Given[TestSeedingSession, ASessionAndACaller]:
        return ASessionToRead(configured=self.configured)

    @override
    def when(self) -> When[ASessionAndACaller, SessionAdapter, AdminSearchSessionsPayload]:
        return SearchingSessions()

    @override
    def then(self) -> Then[ASessionAndACaller, AdminSearchSessionsPayload]:
        return TheWholeSessionIsReturned()


@pytest.mark.parametrize(
    "scenario",
    [
        SessionSchedulingConditionsArePreserved(configured=True),
        SessionSchedulingConditionsArePreserved(configured=False),
    ],
    ids=lambda scenario: scenario.summary(),
)
async def test_searching_details(
    scenario: SessionSchedulingConditionsArePreserved,
    adapter: SessionAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
