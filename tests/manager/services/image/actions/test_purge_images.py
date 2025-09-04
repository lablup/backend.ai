from unittest.mock import AsyncMock

import pytest

from ai.backend.common.dto.agent.response import PurgeImageResp, PurgeImagesResp
from ai.backend.common.types import AgentId
from ai.backend.manager.services.image.actions.purge_images import (
    PurgedImagesData,
    PurgeImagesAction,
    PurgeImagesActionResult,
    PurgeImagesKeyData,
)
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.types import ImageRefData

from ...fixtures import (
    IMAGE_FIXTURE_DICT,
    IMAGE_ROW_FIXTURE,
)
from ...utils import ScenarioBase


@pytest.fixture
def mock_agent_purge_images_rpc(mocker, mock_agent_responses_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.purge_images",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_responses_result
    return mock


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Success Case",
            PurgeImagesAction(
                keys=[
                    PurgeImagesKeyData(
                        agent_id=AgentId("agent_id"),
                        images=[
                            ImageRefData(
                                name=IMAGE_ROW_FIXTURE.name,
                                registry=IMAGE_ROW_FIXTURE.registry,
                                architecture=IMAGE_ROW_FIXTURE.architecture,
                            )
                        ],
                    )
                ],
                force=False,
                noprune=True,
            ),
            PurgeImagesActionResult(
                total_reserved_bytes=IMAGE_ROW_FIXTURE.size_bytes,
                purged_images=[
                    PurgedImagesData(
                        agent_id=AgentId("agent_id"),
                        purged_images=[IMAGE_ROW_FIXTURE.name],
                    )
                ],
                errors=[],
            ),
        ),
    ],
)
@pytest.mark.parametrize(
    "mock_agent_responses_result",
    [
        PurgeImagesResp(
            responses=[
                PurgeImageResp(
                    image=IMAGE_ROW_FIXTURE.name,
                    error=None,
                )
            ]
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "images": [
                IMAGE_FIXTURE_DICT,
            ]
        }
    ],
)
async def test_purge_images(
    mock_agent_purge_images_rpc,
    processors: ImageProcessors,
    test_scenario: ScenarioBase[PurgeImagesAction, PurgeImagesActionResult],
):
    await test_scenario.test(processors.purge_images.wait_for_complete)
