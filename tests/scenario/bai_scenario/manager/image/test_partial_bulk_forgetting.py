"""이미지 여럿 소프트 삭제, 복원."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.image.request import (
    PartialBulkDeleteImagesInput,
    PartialBulkRestoreImagesInput,
)
from ai.backend.common.dto.manager.v2.image.response import ImageNode
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.image import (
    NOTHING,
    EveryImageComesBack,
    ManyImagesAndACaller,
    ManyImagesAndSomeone,
    NoImageIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Forgotten = PartialBulkPayload[ImageNode]
type ImageStep = Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Forgotten]


@dataclass(frozen=True)
class ForgettingEveryTarget(When[ManyImagesAndACaller, ImageAdapter, Forgotten]):
    """대상 이미지들을 한 번에 소프트 삭제한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_delete"

    @override
    def describe(self, laid: ManyImagesAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 이미지 {len(laid.laid)}개{besides}를 한 번에 소프트 삭제"

    @override
    async def call(self, adapter: ImageAdapter, laid: ManyImagesAndACaller) -> Forgotten:
        ids: list[UUID] = [image.id for image in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_delete(PartialBulkDeleteImagesInput(ids=ids))


@dataclass(frozen=True)
class ForgettingThenRestoringEveryTarget(When[ManyImagesAndACaller, ImageAdapter, Forgotten]):
    """대상 이미지들을 한 번에 소프트 삭제했다가 한 번에 복원한다. 복원의 답을 준다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_restore"

    @override
    def describe(self, laid: ManyImagesAndACaller) -> str:
        return (
            f"{laid.caller.username}이 이미지 {len(laid.laid)}개를 한 번에 소프트 삭제했다가 "
            "한 번에 복원"
        )

    @override
    async def call(self, adapter: ImageAdapter, laid: ManyImagesAndACaller) -> Forgotten:
        ids: list[UUID] = [image.id for image in laid.laid]
        with ActingAs(laid.caller):
            await adapter.partial_bulk_delete(PartialBulkDeleteImagesInput(ids=ids))
            return await adapter.partial_bulk_restore(PartialBulkRestoreImagesInput(ids=ids))


@dataclass(frozen=True)
class ForgettingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Forgotten]
):
    @override
    def summary(self) -> str:
        return "forgetting-several-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "살아 있는 이미지 둘과 없는 id 하나를 한 번에 소프트 삭제하면, 둘은 삭제됨 상태로 오고 "
            "없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Forgotten]:
        return ForgettingEveryTarget(missing=NOTHING)

    @override
    def then(self) -> Then[ManyImagesAndACaller, Forgotten]:
        return EveryImageComesBack(status=ImageStatus.DELETED, missing=NOTHING)


@dataclass(frozen=True)
class AUserGrantedNothingForgetsNone(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Forgotten]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-forgets-none-of-several-images"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 이미지 여럿을 한 번에 소프트 삭제하려 하면, "
            "삭제된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Forgotten]:
        return ForgettingEveryTarget()

    @override
    def then(self) -> Then[ManyImagesAndACaller, Forgotten]:
        return NoImageIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class RestoringBringsSeveralBack(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Forgotten]
):
    @override
    def summary(self) -> str:
        return "restoring-several-brings-them-back-alive"

    @override
    def describe(self) -> str:
        return "소프트 삭제한 이미지 여럿을 한 번에 복원하면, 모두 살아 있는 상태로 온다"

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Forgotten]:
        return ForgettingThenRestoringEveryTarget()

    @override
    def then(self) -> Then[ManyImagesAndACaller, Forgotten]:
        return EveryImageComesBack(status=ImageStatus.ALIVE)


SCENARIOS: list[ImageStep] = [
    ForgettingAnswersForTheMissingOne(),
    AUserGrantedNothingForgetsNone(),
    RestoringBringsSeveralBack(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_forgetting(
    scenario: ImageStep, adapter: ImageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
