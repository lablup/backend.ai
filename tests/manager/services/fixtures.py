import dataclasses
import uuid

from dateutil.parser import isoparse

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow, ImageStatus, ImageType

IMAGE_ROW_FIXTURE = ImageRow(
    name="registry.example.com/test_project/python:3.9-ubuntu20.04",
    image="test_project/python",
    project="test_project",
    registry="registry.example.com",
    registry_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    architecture="x86_64",
    accelerators="cuda",
    config_digest="sha256:abcdefgh0123456789abcdefgh0123456789abcdefgh0123456789abcd".ljust(
        72, " "
    ),  # config_digest column is sa.CHAR(length=72)
    size_bytes=12345678,
    is_local=False,
    type=ImageType.COMPUTE,
    labels={},
    resources={},
    status=ImageStatus.ALIVE,
)
IMAGE_ROW_FIXTURE.id = uuid.uuid4()
IMAGE_ROW_FIXTURE.created_at = isoparse("2023-10-01T00:00:00+09:00")

IMAGE_FIXTURE_DATA = IMAGE_ROW_FIXTURE.to_dataclass()

IMAGE_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(IMAGE_FIXTURE_DATA, type=ImageType.COMPUTE._name_, labels={}, resources={})  # type: ignore
)

IMAGE_ALIAS_ROW_FIXTURE = ImageAliasRow(
    id=uuid.uuid4(),
    alias="python",
    image_id=IMAGE_ROW_FIXTURE.id,
)

IMAGE_ALIAS_DATA = IMAGE_ALIAS_ROW_FIXTURE.to_dataclass()
IMAGE_ALIAS_DICT = dataclasses.asdict(IMAGE_ALIAS_DATA)
IMAGE_ALIAS_DICT["image"] = IMAGE_ALIAS_ROW_FIXTURE.image_id

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
