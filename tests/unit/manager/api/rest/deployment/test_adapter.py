"""Unit tests for REST deployment adapter conversions."""

from __future__ import annotations

from uuid import uuid4

import pytest

from ai.backend.common.dto.manager.deployment import (
    ClusterConfigInput,
    ImageInput,
    ModelMountConfigInput,
    ModelRuntimeConfigInput,
    ResourceConfigInput,
    RevisionInput,
)
from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.api.rest.deployment.adapter import build_revision_creator


def _make_revision_input(*, auto_activate: bool) -> RevisionInput:
    return RevisionInput(
        cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
        resource_config=ResourceConfigInput(
            resource_group="default",
            resource_slots={"cpu": "1"},
        ),
        image=ImageInput(id=uuid4()),
        model_runtime_config=ModelRuntimeConfigInput(runtime_variant=RuntimeVariant("custom")),
        model_mount_config=ModelMountConfigInput(
            vfolder_id=uuid4(),
            definition_path="model-definition.yaml",
        ),
        auto_activate=auto_activate,
    )


class TestBuildRevisionCreator:
    """Tests for build_revision_creator auto_activate wiring."""

    @pytest.mark.parametrize("auto_activate", [True, False])
    def test_auto_activate_is_propagated(self, auto_activate: bool) -> None:
        revision_input = _make_revision_input(auto_activate=auto_activate)

        creator = build_revision_creator(revision_input)

        assert creator.auto_activate is auto_activate

    def test_auto_activate_defaults_to_false(self) -> None:
        revision_input = RevisionInput(
            cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
            resource_config=ResourceConfigInput(
                resource_group="default",
                resource_slots={"cpu": "1"},
            ),
            image=ImageInput(id=uuid4()),
            model_runtime_config=ModelRuntimeConfigInput(runtime_variant=RuntimeVariant("custom")),
            model_mount_config=ModelMountConfigInput(
                vfolder_id=uuid4(),
                definition_path="model-definition.yaml",
            ),
        )

        creator = build_revision_creator(revision_input)

        assert creator.auto_activate is False
