import pytest

from ai.backend.manager.services.artifact.actions.get import (
    GetArtifactAction,
    GetArtifactActionResult,
)
from ai.backend.manager.services.artifact.processors import ArtifactProcessors

from ...fixtures import (
    ARTIFACT_FIXTURE_DATA,
    ARTIFACT_FIXTURE_DICT,
    ARTIFACT_ROW_FIXTURE,
)
from ...utils import ScenarioBase


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Success Case",
            GetArtifactAction(
                artifact_id=ARTIFACT_ROW_FIXTURE.id,
            ),
            GetArtifactActionResult(
                result=ARTIFACT_FIXTURE_DATA,
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
async def test_get_artifact(
    processors: ArtifactProcessors,
    test_scenario: ScenarioBase[GetArtifactAction, GetArtifactActionResult],
):
    await test_scenario.test(processors.get.wait_for_complete)
