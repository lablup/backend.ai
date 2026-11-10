"""아티팩트 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact.request import UpdateArtifactInput
from ai.backend.common.dto.manager.v2.artifact.response import ArtifactNode
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.errors.artifact import ArtifactNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.artifact import (
    AnArtifactAndACaller,
    AnArtifactAndSomeone,
    ArtifactLook,
    TheArtifactNode,
)
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = Says("수정한 설명", english="the edited description")

type ArtifactStep = Scenario[
    TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, ArtifactNode
]


@dataclass(frozen=True)
class Editing(When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]):
    """아티팩트의 설명을 고친다. `deleted_first`면 먼저 soft delete 한다."""

    deleted_first: bool = False

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: AnArtifactAndACaller) -> str:
        who = laid.caller.username
        if self.deleted_first:
            return Says(
                f"{who}이 {laid.artifact.name}을 soft delete 한 뒤 설명을 수정합니다",
                english=f"{who} soft deletes {laid.artifact.name} and then changes its description",
            )
        return Says(
            f"{who}이 {laid.artifact.name}의 설명을 수정합니다",
            english=f"{who} changes the description of {laid.artifact.name}",
        )

    @override
    async def call(self, adapter: ArtifactAdapter, laid: AnArtifactAndACaller) -> ArtifactNode:
        with ActingAs(laid.caller):
            if self.deleted_first:
                await adapter.delete(ArtifactID(laid.artifact.id))
            payload = await adapter.update(
                UpdateArtifactInput(description=EDITED), laid.artifact.id
            )
            return payload.artifact


@dataclass(frozen=True)
class TheSuperadminEditsAnArtifact(
    Scenario[TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-an-artifact"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아티팩트의 설명을 변경하면, 새 설명을 담은 아티팩트가 응답으로 옵니다",
            english=(
                "when the superadmin changes the description of an artifact, the artifact "
                "comes back holding the new description"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactAndACaller]:
        return AnArtifactAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]:
        return Editing()

    @override
    def then(self) -> Then[AnArtifactAndACaller, ArtifactNode]:
        return TheArtifactNode(started=self.started, expected=ArtifactLook(described=EDITED))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-an-artifact"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 아티팩트를 수정할 수 없습니다",
            english="a user granted nothing cannot edit an artifact",
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactAndACaller]:
        return AnArtifactAndSomeone()

    @override
    def when(self) -> When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]:
        return Editing()

    @override
    def then(self) -> Then[AnArtifactAndACaller, ArtifactNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ASoftDeletedArtifactIsNotEdited(
    Scenario[TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]
):
    @override
    def summary(self) -> str:
        return "a-soft-deleted-artifact-is-not-edited"

    @override
    def describe(self) -> str:
        return Says(
            "soft delete 된 아티팩트는 superadmin 이라도 수정할 수 없고, 대상이 없다는 것으로 "
            "거부됩니다",
            english=(
                "a soft-deleted artifact cannot be edited even by the superadmin, and it is "
                "rejected as having no target"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactAndACaller]:
        return AnArtifactAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]:
        return Editing(deleted_first=True)

    @override
    def then(self) -> Then[AnArtifactAndACaller, ArtifactNode]:
        return TheCallIsRefused(ArtifactNotFoundError)


SCENARIOS: list[ArtifactStep] = [
    TheSuperadminEditsAnArtifact(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotEdit(),
    ASoftDeletedArtifactIsNotEdited(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: ArtifactStep, adapter: ArtifactAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
