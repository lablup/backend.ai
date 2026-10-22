"""이미지 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.image.request import (
    PartialBulkUpdateImageItemInput,
    PartialBulkUpdateImagesInput,
    UpdateImageBody,
)
from ai.backend.common.dto.manager.v2.image.response import ImageNode
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.image import (
    EveryImageComesBack,
    ManyImagesAndACaller,
    ManyImagesAndSomeone,
    NoImageIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED_TAG = "edited-together"

type Edited = PartialBulkPayload[ImageNode]
type ImageStep = Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Edited]


@dataclass(frozen=True)
class EditingEveryTarget(When[ManyImagesAndACaller, ImageAdapter, Edited]):
    """대상 이미지들의 태그를 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyImagesAndACaller) -> str:
        return f"{laid.caller.username}이 이미지 {len(laid.laid)}개의 태그를 한 번에 고침"

    @override
    async def call(self, adapter: ImageAdapter, laid: ManyImagesAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateImagesInput(
                    items=[
                        PartialBulkUpdateImageItemInput(
                            id=image.id, input=UpdateImageBody(tag=EDITED_TAG)
                        )
                        for image in laid.laid
                    ]
                )
            )


@dataclass(frozen=True)
class TheSuperadminEditsSeveralImages(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-images-at-once"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 이미지 여럿의 태그를 한 번에 바꾸면, 모두 새 태그로 오고 실패한 것은 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyImagesAndACaller, Edited]:
        return EveryImageComesBack(tag=EDITED_TAG)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-images"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 이미지 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyImagesAndACaller, Edited]:
        return NoImageIsProcessed(reason="Insufficient permission")


SCENARIOS: list[ImageStep] = [
    TheSuperadminEditsSeveralImages(),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: ImageStep, adapter: ImageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
