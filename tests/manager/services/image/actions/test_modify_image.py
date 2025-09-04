from dataclasses import replace

import pytest

from ai.backend.common.types import SlotName
from ai.backend.manager.data.image.types import ImageLabelsData, ImageResourcesData
from ai.backend.manager.errors.image import ImageNotFound, ModifyImageActionValueError
from ai.backend.manager.models.image import ImageType
from ai.backend.manager.services.image.actions.modify_image import (
    ImageModifier,
    ModifyImageAction,
    ModifyImageActionResult,
)
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.types import OptionalState, TriState

from ...fixtures import (
    IMAGE_ALIAS_DICT,
    IMAGE_ALIAS_ROW_FIXTURE,
    IMAGE_FIXTURE_DATA,
    IMAGE_FIXTURE_DICT,
    IMAGE_ROW_FIXTURE,
)
from ...utils import ScenarioBase


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Update one column",
            ModifyImageAction(
                target=IMAGE_ROW_FIXTURE.name,
                architecture=IMAGE_ROW_FIXTURE.architecture,
                modifier=ImageModifier(
                    registry=OptionalState.update("cr.backend.ai2"),
                ),
            ),
            ModifyImageActionResult(image=replace(IMAGE_FIXTURE_DATA, registry="cr.backend.ai2")),
        ),
        ScenarioBase.success(
            "Make a column empty",
            ModifyImageAction(
                target=IMAGE_ROW_FIXTURE.name,
                architecture=IMAGE_ROW_FIXTURE.architecture,
                modifier=ImageModifier(
                    accelerators=TriState.nullify(),
                ),
            ),
            ModifyImageActionResult(image=replace(IMAGE_FIXTURE_DATA, accelerators=None)),
        ),
        ScenarioBase.success(
            "Update multiple columns",
            ModifyImageAction(
                target=IMAGE_ROW_FIXTURE.name,
                architecture=IMAGE_ROW_FIXTURE.architecture,
                modifier=ImageModifier(
                    type=OptionalState.update(ImageType.SERVICE),
                    registry=OptionalState.update("cr.backend.ai2"),
                    accelerators=TriState.update(value="cuda,rocm"),
                    is_local=OptionalState.update(True),
                    size_bytes=OptionalState.update(123),
                    labels=OptionalState.update({"ai.backend.resource.min.mem": "128m"}),
                    resources=OptionalState.update(
                        {
                            "cpu": {"min": "3", "max": "5"},
                            "mem": {"min": "256m", "max": None},
                            "cuda.device": {"max": None, "min": "1"},
                        },
                    ),
                    config_digest=OptionalState.update("sha256:1234567890abcdef"),
                ),
            ),
            ModifyImageActionResult(
                image=replace(
                    IMAGE_FIXTURE_DATA,
                    type=ImageType.SERVICE,
                    registry="cr.backend.ai2",
                    accelerators="cuda,rocm",
                    is_local=True,
                    size_bytes=123,
                    labels=ImageLabelsData(label_data={"ai.backend.resource.min.mem": "128m"}),
                    resources=ImageResourcesData(
                        resources_data={
                            SlotName("cpu"): {"min": "3", "max": "5"},
                            SlotName("mem"): {"min": "256m", "max": None},
                            SlotName("cuda.device"): {"max": None, "min": "1"},
                        }
                    ),
                    config_digest="sha256:1234567890abcdef",
                )
            ),
        ),
        ScenarioBase.success(
            "Update one column by image alias",
            ModifyImageAction(
                target=IMAGE_ALIAS_ROW_FIXTURE.alias,
                architecture=IMAGE_ROW_FIXTURE.architecture,
                modifier=ImageModifier(
                    registry=OptionalState.update("cr.backend.ai2"),
                ),
            ),
            ModifyImageActionResult(image=replace(IMAGE_FIXTURE_DATA, registry="cr.backend.ai2")),
        ),
        ScenarioBase.failure(
            "Image not found",
            ModifyImageAction(
                target="wrong-image",
                architecture=IMAGE_ROW_FIXTURE.architecture,
                modifier=ImageModifier(
                    registry=OptionalState.update("cr.backend.ai2"),
                ),
            ),
            ImageNotFound,
        ),
        ScenarioBase.failure(
            "Value Error",
            ModifyImageAction(
                target=IMAGE_ROW_FIXTURE.name,
                architecture=IMAGE_ROW_FIXTURE.architecture,
                modifier=ImageModifier(
                    config_digest=OptionalState.update(
                        "a" * 73
                    ),  # config_digest column is sa.CHAR(length=72)
                ),
            ),
            ModifyImageActionValueError,
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "images": [
                IMAGE_FIXTURE_DICT,
            ],
            "image_aliases": [
                IMAGE_ALIAS_DICT,
            ],
        }
    ],
)
async def test_modify_image(
    processors: ImageProcessors,
    test_scenario: ScenarioBase[ModifyImageAction, ModifyImageActionResult],
):
    await test_scenario.test(processors.modify_image.wait_for_complete)
