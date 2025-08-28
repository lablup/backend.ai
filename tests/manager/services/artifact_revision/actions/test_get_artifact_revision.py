import pytest

from ai.backend.manager.services.artifact_revision.actions.get import (
    GetArtifactRevisionAction,
    GetArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.processors import ArtifactRevisionProcessors

from ...fixtures import (
    ARTIFACT_FIXTURE_DICT,
    ARTIFACT_REVISION_FIXTURE_DATA,
    ARTIFACT_REVISION_FIXTURE_DICT,
    ARTIFACT_REVISION_ROW_FIXTURE,
)
from ...utils import ScenarioBase


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Success Case",
            GetArtifactRevisionAction(
                artifact_revision_id=ARTIFACT_REVISION_ROW_FIXTURE.id,
            ),
            GetArtifactRevisionActionResult(
                revision=ARTIFACT_REVISION_FIXTURE_DATA,
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
async def test_get_artifact_revision(
    processors: ArtifactRevisionProcessors,
    test_scenario: ScenarioBase[GetArtifactRevisionAction, GetArtifactRevisionActionResult],
):
    await test_scenario.test(processors.get.wait_for_complete)
