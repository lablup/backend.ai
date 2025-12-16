import pytest

from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.services.artifact_revision.actions.search import (
    SearchArtifactRevisionsAction,
    SearchArtifactRevisionsActionResult,
)
from ai.backend.manager.services.artifact_revision.processors import ArtifactRevisionProcessors

from ...fixtures import (
    ARTIFACT_FIXTURE_DICT,
    ARTIFACT_REVISION_FIXTURE_DATA,
    ARTIFACT_REVISION_FIXTURE_DICT,
)
from ...utils import ScenarioBase


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Success Case - Search all artifact revisions",
            SearchArtifactRevisionsAction(
                querier=BatchQuerier(
                    conditions=[],
                    orders=[],
                    pagination=OffsetPagination(limit=10, offset=0),
                ),
            ),
            SearchArtifactRevisionsActionResult(
                data=[ARTIFACT_REVISION_FIXTURE_DATA],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            ),
        ),
        ScenarioBase.success(
            "Success Case - Search with ordering",
            SearchArtifactRevisionsAction(
                querier=BatchQuerier(
                    conditions=[],
                    orders=[],
                    pagination=OffsetPagination(limit=10, offset=0),
                ),
            ),
            SearchArtifactRevisionsActionResult(
                data=[ARTIFACT_REVISION_FIXTURE_DATA],
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
            "artifact_revisions": [ARTIFACT_REVISION_FIXTURE_DICT],
        }
    ],
)
async def test_search_artifact_revisions(
    processors: ArtifactRevisionProcessors,
    test_scenario: ScenarioBase[SearchArtifactRevisionsAction, SearchArtifactRevisionsActionResult],
):
    await test_scenario.test(processors.search_revision.wait_for_complete)
