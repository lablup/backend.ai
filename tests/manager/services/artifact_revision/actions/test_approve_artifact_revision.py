import dataclasses

import pytest

from ai.backend.manager.data.artifact.types import ArtifactStatus
from ai.backend.manager.services.artifact_revision.actions.approve import (
    ApproveArtifactRevisionAction,
    ApproveArtifactRevisionActionResult,
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
            ApproveArtifactRevisionAction(
                artifact_revision_id=ARTIFACT_REVISION_ROW_FIXTURE.id,
            ),
            ApproveArtifactRevisionActionResult(
                result=dataclasses.replace(
                    ARTIFACT_REVISION_FIXTURE_DATA,
                    status=ArtifactStatus.AVAILABLE,
                ),
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
async def test_approve_artifact_revision(
    processors: ArtifactRevisionProcessors,
    test_scenario: ScenarioBase[ApproveArtifactRevisionAction, ApproveArtifactRevisionActionResult],
):
    await test_scenario.test(processors.approve.wait_for_complete)
