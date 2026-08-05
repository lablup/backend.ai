"""Tests for ImageRow.to_dataclass()."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest

from ai.backend.common.types import ImageID
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow

# ORM cluster registration: instantiating ImageRow triggers configure_mappers(),
# which resolves string relationships against the registry. These rows are
# reachable via relationships but are not otherwise imported by this test.
_ORM_CLUSTER = (
    AgentRow,
    ContainerRegistryRow,
    ImageAliasRow,
    ScalingGroupForProjectRow,
)

_REGISTRY = "cr.backend.ai"
_PROJECT = "stable"
_IMAGE = "python"


@dataclass(frozen=True)
class _TagCase:
    tag: str
    expected_version: str


class TestImageRowToDataclass:
    @pytest.fixture
    def image_row(self, case: _TagCase) -> ImageRow:
        row = ImageRow(
            name=f"{_REGISTRY}/{_PROJECT}/{_IMAGE}:{case.tag}",
            project=_PROJECT,
            architecture="x86_64",
            registry_id=uuid4(),
            registry=_REGISTRY,
            image=f"{_PROJECT}/{_IMAGE}",
            tag=case.tag,
            config_digest="sha256:abc123".ljust(72, " "),
            size_bytes=1024,
            type=ImageType.COMPUTE,
            labels={},
            resources={},
            status=ImageStatus.ALIVE,
        )
        row.id = ImageID(uuid4())
        return row

    @pytest.mark.parametrize(
        "case",
        [
            _TagCase(tag="3.11", expected_version="3.11"),
            _TagCase(tag="3.11-ubuntu20.04", expected_version="3.11"),
            _TagCase(tag="3.11-ubuntu20.04-cuda12.1", expected_version="3.11"),
            _TagCase(tag="latest", expected_version="latest"),
        ],
        ids=lambda case: case.tag,
    )
    def test_registry_tag_and_version_are_exposed(
        self, image_row: ImageRow, case: _TagCase
    ) -> None:
        data = image_row.to_dataclass()

        assert data.registry == _REGISTRY
        assert data.tag == case.tag
        assert data.version == case.expected_version
