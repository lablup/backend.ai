import pytest

from ai.backend.manager.repositories.artifact.types import (
    ArtifactRevisionOrderingOptions,
)
from ai.backend.manager.repositories.types import PaginationOptions
from ai.backend.manager.services.artifact_revision.actions.list import (
    ListArtifactRevisionsAction,
    ListArtifactRevisionsActionResult,
)
from ai.backend.manager.services.artifact_revision.processors import ArtifactRevisionProcessors
from ai.backend.manager.types import OffsetBasedPaginationOptions

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
            "Success Case - List all artifact revisions",
            ListArtifactRevisionsAction(
                pagination=PaginationOptions(
                    offset=OffsetBasedPaginationOptions(
                        limit=10,
                        offset=0,
                    )
                ),
            ),
            ListArtifactRevisionsActionResult(
                data=[ARTIFACT_REVISION_FIXTURE_DATA],
                total_count=1,
            ),
        ),
        ScenarioBase.success(
            "Success Case - List with ordering",
            ListArtifactRevisionsAction(
                pagination=PaginationOptions(
                    offset=OffsetBasedPaginationOptions(
                        limit=10,
                        offset=0,
                    )
                ),
                ordering=ArtifactRevisionOrderingOptions(),
            ),
            ListArtifactRevisionsActionResult(
                data=[ARTIFACT_REVISION_FIXTURE_DATA],
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
            "artifact_revisions": [ARTIFACT_REVISION_FIXTURE_DICT],
        }
    ],
)
async def test_list_artifact_revisions(
    processors: ArtifactRevisionProcessors,
    test_scenario: ScenarioBase[ListArtifactRevisionsAction, ListArtifactRevisionsActionResult],
):
    await test_scenario.test(processors.list_revision.wait_for_complete)
