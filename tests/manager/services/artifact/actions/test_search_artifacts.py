import pytest

from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.services.artifact.actions.search import (
    SearchArtifactsAction,
    SearchArtifactsActionResult,
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
            "Success Case - Search all artifacts",
            SearchArtifactsAction(
                querier=BatchQuerier(
                    conditions=[],
                    orders=[],
                    pagination=OffsetPagination(limit=10, offset=0),
                ),
            ),
            SearchArtifactsActionResult(
                data=[ARTIFACT_FIXTURE_DATA],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            ),
        ),
        ScenarioBase.success(
            "Success Case - Search with ordering",
            SearchArtifactsAction(
                querier=BatchQuerier(
                    conditions=[],
                    orders=[],
                    pagination=OffsetPagination(limit=10, offset=0),
                ),
            ),
            SearchArtifactsActionResult(
                data=[ARTIFACT_FIXTURE_DATA],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
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
async def test_search_artifacts(
    processors: ArtifactProcessors,
    test_scenario: ScenarioBase[SearchArtifactsAction, SearchArtifactsActionResult],
):
    await test_scenario.test(processors.search_artifacts.wait_for_complete)
