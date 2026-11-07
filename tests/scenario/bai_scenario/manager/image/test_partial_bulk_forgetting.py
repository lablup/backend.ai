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

type Forgotten = PartialBulkPayload[ImageNode]
type ImageStep = Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Forgotten]


@dataclass(frozen=True)
class ForgettingEveryTarget(When[ManyImagesAndACaller, ImageAdapter, Forgotten]):
    """대상 이미지들을 한 번에 소프트 삭제한다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_delete"

    @override
    def describe(self, laid: ManyImagesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 이미지 {len(laid.laid)}개를 한 번에 소프트 삭제합니다",
            english=f"{laid.caller.username} soft deletes {len(laid.laid)} images at once",
        )

    @override
    async def call(self, adapter: ImageAdapter, laid: ManyImagesAndACaller) -> Forgotten:
        ids: list[UUID] = [image.id for image in laid.laid]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_delete(PartialBulkDeleteImagesInput(ids=ids))


@dataclass(frozen=True)
class RestoringEveryTarget(When[ManyImagesAndACaller, ImageAdapter, Forgotten]):
    """대상 이미지들을 한 번에 복원한다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_restore"

    @override
    def describe(self, laid: ManyImagesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 이미지 {len(laid.laid)}개를 한 번에 복원합니다",
            english=f"{laid.caller.username} restores {len(laid.laid)} images at once",
        )

    @override
    async def call(self, adapter: ImageAdapter, laid: ManyImagesAndACaller) -> Forgotten:
        ids: list[UUID] = [image.id for image in laid.laid]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_restore(PartialBulkRestoreImagesInput(ids=ids))


@dataclass(frozen=True)
class AUserGrantedSoftDeleteForgetsEveryTarget(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Forgotten]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-soft-delete-forgets-several-images-at-once"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리에서 이미지 소프트 삭제 권한을 받은 사용자가 이미지 여럿을 한 번에 "
            "소프트 삭제하면 모두 삭제됨 상태로 오고 실패한 것은 없습니다",
            english=(
                "when a user granted soft delete on the registry's images soft deletes several "
                "images at once, they all come back as deleted and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(role=UserRole.USER, granted=(Permission.SOFT_DELETE,))

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Forgotten]:
        return ForgettingEveryTarget()

    @override
    def then(self) -> Then[ManyImagesAndACaller, Forgotten]:
        return EveryImageComesBack(status=ImageStatus.DELETED)


@dataclass(frozen=True)
class AUserWithoutSoftDeleteOnAnothersImageForgetsOnlyTheirOwn(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Forgotten]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-soft-delete-is-denied-on-another-users-image"

    @override
    def describe(self) -> str:
        return Says(
            "자기 개인 프로젝트에서 이미지 소프트 삭제 권한을 받은 사용자가 자기 이미지와 다른 "
            "사용자의 이미지를 한 번에 소프트 삭제하면, 자기 이미지만 삭제됨 상태로 오고 다른 "
            "사용자의 이미지는 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted soft delete in their own personal project soft deletes "
                "their own image and another user's image at once, only their own comes back "
                "as deleted and the other comes back in the failed list for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return CustomImagesOfTwoMakers(granted=Permission.SOFT_DELETE)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Forgotten]:
        return ForgettingEveryTarget()

    @override
    def then(self) -> Then[ManyImagesAndACaller, Forgotten]:
        return OneImageIsNotProcessed(status=ImageStatus.DELETED, reason="Insufficient permission")


@dataclass(frozen=True)
class AnAlreadyDeletedImageIsNotForgotten(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Forgotten]
):
    @override
    def summary(self) -> str:
        return "forgetting-several-leaves-the-already-deleted-one"

    @override
    def describe(self) -> str:
        return Says(
            "살아 있는 이미지와 이미 삭제된 이미지를 한 번에 소프트 삭제하면, 살아 있는 것만 "
            "삭제됨 상태로 오고 이미 삭제된 것은 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "soft deleting an alive image and an already deleted image at once brings the "
                "alive one back as deleted, and the already deleted one comes back in the "
                "failed list as not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(
            role=UserRole.USER,
            statuses=(ImageStatus.ALIVE, ImageStatus.DELETED),
            granted=(Permission.SOFT_DELETE,),
        )

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Forgotten]:
        return ForgettingEveryTarget()

    @override
    def then(self) -> Then[ManyImagesAndACaller, Forgotten]:
        return OneImageIsNotProcessed(status=ImageStatus.DELETED, reason="not found")


@dataclass(frozen=True)
class RestoringBringsSeveralBack(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Forgotten]
):
    @override
    def summary(self) -> str:
        return "restoring-several-brings-them-back-alive"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리에서 이미지 소프트 삭제 권한을 받은 사용자가 삭제된 이미지 여럿을 한 번에 "
            "복원하면 모두 살아 있는 상태로 오고 실패한 것은 없습니다",
            english=(
                "when a user granted soft delete on the registry's images restores several "
                "deleted images at once, they all come back alive and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(
            role=UserRole.USER,
            statuses=(ImageStatus.DELETED, ImageStatus.DELETED),
            granted=(Permission.SOFT_DELETE,),
        )

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Forgotten]:
        return RestoringEveryTarget()

    @override
    def then(self) -> Then[ManyImagesAndACaller, Forgotten]:
        return EveryImageComesBack(status=ImageStatus.ALIVE)


@dataclass(frozen=True)
class AUserWithoutSoftDeleteOnAnothersImageRestoresOnlyTheirOwn(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Forgotten]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-soft-delete-restores-only-their-own-image"

    @override
    def describe(self) -> str:
        return Says(
            "자기 개인 프로젝트에서 이미지 소프트 삭제 권한을 받은 사용자가 자기 이미지와 다른 "
            "사용자의 이미지를 한 번에 복원하면, 자기 이미지만 살아 있는 상태로 오고 다른 "
            "사용자의 이미지는 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted soft delete in their own personal project restores their "
                "own image and another user's image at once, only their own comes back alive "
                "and the other comes back in the failed list for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return CustomImagesOfTwoMakers(
            own_status=ImageStatus.DELETED, granted=Permission.SOFT_DELETE
        )

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Forgotten]:
        return RestoringEveryTarget()

    @override
    def then(self) -> Then[ManyImagesAndACaller, Forgotten]:
        return OneImageIsNotProcessed(status=ImageStatus.ALIVE, reason="Insufficient permission")


@dataclass(frozen=True)
class AnImageBeingPurgedIsNotRestored(
    Scenario[TestSeedingSession, ManyImagesAndACaller, ImageAdapter, Forgotten]
):
    @override
    def summary(self) -> str:
        return "restoring-several-leaves-the-one-being-purged"

    @override
    def describe(self) -> str:
        return Says(
            "삭제된 이미지와 완전 삭제 중인 이미지를 한 번에 복원하면, 삭제된 것만 살아 있는 "
            "상태로 오고 완전 삭제 중인 것은 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "restoring a deleted image and an image being purged at once brings the deleted "
                "one back alive, and the one being purged comes back in the failed list as "
                "not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(
            role=UserRole.USER,
            statuses=(ImageStatus.DELETED, ImageStatus.PURGING),
            granted=(Permission.SOFT_DELETE,),
        )

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, Forgotten]:
        return RestoringEveryTarget()

    @override
    def then(self) -> Then[ManyImagesAndACaller, Forgotten]:
        return OneImageIsNotProcessed(status=ImageStatus.ALIVE, reason="not found")


SCENARIOS: list[ImageStep] = [
    AUserGrantedSoftDeleteForgetsEveryTarget(),
    AUserWithoutSoftDeleteOnAnothersImageForgetsOnlyTheirOwn(),
    AnAlreadyDeletedImageIsNotForgotten(),
    RestoringBringsSeveralBack(),
    AUserWithoutSoftDeleteOnAnothersImageRestoresOnlyTheirOwn(),
    AnImageBeingPurgedIsNotRestored(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_forgetting(
    scenario: ImageStep, adapter: ImageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
