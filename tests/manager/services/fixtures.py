import dataclasses
import uuid
from datetime import datetime, timezone

from dateutil.parser import isoparse

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow, ImageStatus, ImageType
from ai.backend.testutils.mock import mock_aioresponses_sequential_payloads

RESOURCE_LIMITS = {"cuda.device": {"min": "1", "max": None}}

CONTAINER_REGISTRY_ROW_FIXTURE = ContainerRegistryRow(
    url="https://registry.example.com",
    registry_name="registry.example.com",
    type=ContainerRegistryType.DOCKER,
    project="test_project",
    username=None,
    password=None,
    ssl_verify=True,
    is_global=True,
    extra=None,
)

CONTAINER_REGISTRY_ROW_FIXTURE.id = uuid.uuid4()
CONTAINER_REGISTRY_FIXTURE_DATA = CONTAINER_REGISTRY_ROW_FIXTURE.to_dataclass()
CONTAINER_REGISTRY_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(CONTAINER_REGISTRY_FIXTURE_DATA, type=ContainerRegistryType.DOCKER.value)  # type: ignore
)


IMAGE_ROW_FIXTURE = ImageRow(
    name="registry.example.com/test_project/python:3.9-ubuntu20.04",
    image="test_project/python",
    project="test_project",
    registry="registry.example.com",
    registry_id=CONTAINER_REGISTRY_ROW_FIXTURE.id,
    architecture="x86_64",
    accelerators="cuda",
    config_digest="sha256:abcdefgh0123456789abcdefgh0123456789abcdefgh0123456789abcd".ljust(
        72, " "
    ),  # config_digest column is sa.CHAR(length=72)
    size_bytes=12345678,
    is_local=False,
    type=ImageType.COMPUTE,
    labels={},
    resources=RESOURCE_LIMITS,
    status=ImageStatus.ALIVE,
)
IMAGE_ROW_FIXTURE.id = uuid.uuid4()
IMAGE_ROW_FIXTURE.created_at = datetime(2023, 9, 30, 15, 0, 0, tzinfo=timezone.utc)

IMAGE_FIXTURE_DATA = IMAGE_ROW_FIXTURE.to_dataclass()

IMAGE_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(
        IMAGE_FIXTURE_DATA,
        type=ImageType.COMPUTE._name_,  # type: ignore
        labels={},  # type: ignore
        resources=RESOURCE_LIMITS,  # type: ignore
    )
)

IMAGE_ALIAS_ROW_FIXTURE = ImageAliasRow(
    id=uuid.uuid4(),
    alias="python",
    image_id=IMAGE_ROW_FIXTURE.id,
)

IMAGE_ALIAS_DATA = IMAGE_ALIAS_ROW_FIXTURE.to_dataclass()
IMAGE_ALIAS_DICT = dataclasses.asdict(IMAGE_ALIAS_DATA)
IMAGE_ALIAS_DICT["image"] = IMAGE_ALIAS_ROW_FIXTURE.image_id


DOCKERHUB_RESPONSE_MOCK = {
    "get_token": {"token": "fake-token"},
    "get_catalog": {
        "repositories": [
            "test_project/python",
            "other/dangling-image1",
            "other/dangling-image2",
            "other/python",
        ],
    },
    "get_tags": mock_aioresponses_sequential_payloads([
        {"tags": ["latest"]},
        {"tags": []},
        {"tags": None},
        {"tags": ["latest"]},
    ]),
    "get_manifest": {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": 100,
            "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
        },
        "layers": [],
    },
    "get_config": {"architecture": "amd64", "os": "linux"},
}


# Artifact fixtures
HUGGINGFACE_REGISTRY_ID = uuid.uuid4()

ARTIFACT_ROW_FIXTURE = ArtifactRow(
    name="microsoft/DialoGPT-medium",
    type=ArtifactType.MODEL,
    registry_id=HUGGINGFACE_REGISTRY_ID,
    registry_type=ArtifactRegistryType.HUGGINGFACE.value,
    source_registry_id=HUGGINGFACE_REGISTRY_ID,
    source_registry_type=ArtifactRegistryType.HUGGINGFACE.value,
    description="A conversational AI model by Microsoft",
    readonly=True,
    availability=ArtifactAvailability.ALIVE.value,
)
ARTIFACT_ROW_FIXTURE.id = uuid.uuid4()
ARTIFACT_ROW_FIXTURE.scanned_at = datetime.now(timezone.utc)
ARTIFACT_ROW_FIXTURE.updated_at = datetime.now(timezone.utc)

ARTIFACT_FIXTURE_DATA = ARTIFACT_ROW_FIXTURE.to_dataclass()
ARTIFACT_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(
        ARTIFACT_FIXTURE_DATA,
        type=ArtifactType.MODEL.value,  # type: ignore
        registry_type=ArtifactRegistryType.HUGGINGFACE.value,  # type: ignore
        source_registry_type=ArtifactRegistryType.HUGGINGFACE.value,  # type: ignore
    )
)

ARTIFACT_REVISION_ROW_FIXTURE = ArtifactRevisionRow(
    artifact_id=ARTIFACT_ROW_FIXTURE.id,
    version="main",
    readme="# DialoGPT-medium\n\nA conversational AI model.",
    size=1024000,
    status=ArtifactStatus.NEEDS_APPROVAL,
)
ARTIFACT_REVISION_ROW_FIXTURE.id = uuid.uuid4()
ARTIFACT_REVISION_ROW_FIXTURE.created_at = isoparse("2023-10-01T00:00:00+09:00")
ARTIFACT_REVISION_ROW_FIXTURE.updated_at = isoparse("2023-10-01T00:00:00+09:00")

ARTIFACT_REVISION_FIXTURE_DATA = ARTIFACT_REVISION_ROW_FIXTURE.to_dataclass()
ARTIFACT_REVISION_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(
        ARTIFACT_REVISION_FIXTURE_DATA,
        status=ArtifactStatus.NEEDS_APPROVAL.value,  # type: ignore
    )
)
