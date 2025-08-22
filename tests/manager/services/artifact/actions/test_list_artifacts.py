import pytest

from ai.backend.manager.repositories.artifact.repository import ArtifactOrderingOptions
from ai.backend.manager.repositories.types import OffsetBasedPaginationOptions, PaginationOptions
from ai.backend.manager.services.artifact.actions.list import (
    ListArtifactsAction,
    ListArtifactsActionResult,
)
from ai.backend.manager.services.artifact.processors import ArtifactProcessors

from ...fixtures import (
    ARTIFACT_FIXTURE_DATA,
    ARTIFACT_FIXTURE_DICT,
)
from ...utils import ScenarioBase


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Success Case - List all artifacts",
            ListArtifactsAction(
                pagination=PaginationOptions(
                    offset=OffsetBasedPaginationOptions(
                        limit=10,
                        offset=0,
                    )
                ),
            ),
            ListArtifactsActionResult(
                data=[ARTIFACT_FIXTURE_DATA],
                total_count=1,
            ),
        ),
        ScenarioBase.success(
            "Success Case - List with ordering",
            ListArtifactsAction(
                pagination=PaginationOptions(
                    offset=OffsetBasedPaginationOptions(
                        limit=10,
                        offset=0,
                    )
                ),
                ordering=ArtifactOrderingOptions(),
            ),
            ListArtifactsActionResult(
                data=[ARTIFACT_FIXTURE_DATA],
                total_count=1,
            ),
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "artifacts": [ARTIFACT_FIXTURE_DICT],
        }
    ],
)
async def test_list_artifacts(
    processors: ArtifactProcessors,
    test_scenario: ScenarioBase[ListArtifactsAction, ListArtifactsActionResult],
):
    await test_scenario.test(processors.list_artifacts.wait_for_complete)
