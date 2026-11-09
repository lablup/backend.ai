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
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.image import (
    CustomImagesOfTwoMakers,
    EveryImageComesBack,
    ManyImagesAndACaller,
    ManyImagesAndSomeone,
    OneImageIsNotProcessed,
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
        return Says(
            f"{laid.caller.username}이 이미지 {len(laid.laid)}개의 태그를 한 번에 수정합니다",
            english=f"{laid.caller.username} changes the tags of {len(laid.laid)} images at once",
        )

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
class AUserGrantedUpdateEditsEveryTarget(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-edits-several-images-at-once"

    @override
    def describe(self) -> str:
        return Says(
            "이미지 수정 권한을 받은 사용자가 이미지 여럿의 태그를 한 번에 변경하면 모두 새 태그로 "
            "오고 실패한 것은 없습니다",
            english=(
                "when a user granted update on images changes the tags of several images at "
                "once, they all come back with the new tag and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(role=UserRole.USER, granted=(Permission.UPDATE,))

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyImagesAndACaller, Edited]:
        return EveryImageComesBack(tag=EDITED_TAG)


@dataclass(frozen=True)
class AUserWithoutUpdateOnAnothersImageEditsOnlyTheirOwn(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-is-denied-on-another-users-image"

    @override
    def describe(self) -> str:
        return Says(
            "자기 개인 프로젝트에서 이미지 수정 권한을 받은 사용자가 자기 이미지와 다른 사용자의 "
            "이미지를 한 번에 수정하면, 자기 이미지만 새 태그로 오고 다른 사용자의 이미지는 "
            "권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted update in their own personal project changes the tags of "
                "their own image and another user's image at once, only their own comes back "
                "with the new tag and the other comes back in the failed list for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return CustomImagesOfTwoMakers(granted=Permission.UPDATE)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyImagesAndACaller, Edited]:
        return OneImageIsNotProcessed(
            status=ImageStatus.ALIVE, tag=EDITED_TAG, reason="Insufficient permission"
        )


SCENARIOS: list[ImageStep] = [
    AUserGrantedUpdateEditsEveryTarget(),
    AUserWithoutUpdateOnAnothersImageEditsOnlyTheirOwn(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: ImageStep, adapter: ImageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
