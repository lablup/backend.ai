import enum
import re
import uuid
from typing import Any
from urllib.parse import urlparse

from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema

from .api_handlers import BaseFieldModel, BaseRequestModel, BaseResponseModel


class ContainerRegistryType(enum.StrEnum):
    DOCKER = "docker"
    HARBOR = "harbor"
    HARBOR2 = "harbor2"
    GITHUB = "github"
    GITLAB = "gitlab"
    ECR = "ecr"
    ECR_PUB = "ecr-public"
    LOCAL = "local"
    OCP = "ocp"


HARBOR_PROJECT_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")


def validate_registry_url(url: str) -> None:
    """Raise ValueError unless ``url`` parses to a scheme and a host; a bare host
    is read as http."""
    candidate = url.strip()
    if not candidate.startswith(("http://", "https://")):
        candidate = "http://" + candidate
    try:
        parsed = urlparse(candidate)
    except ValueError:
        raise ValueError(f"Invalid URL format: {url}") from None
    if not (parsed.scheme and parsed.netloc):
        raise ValueError(f"Invalid URL format: {url}")


def validate_registry_project(registry_type: ContainerRegistryType, project: str | None) -> None:
    if registry_type not in (ContainerRegistryType.HARBOR, ContainerRegistryType.HARBOR2):
        return
    if project is None:
        raise ValueError("Project name is required for Harbor.")
    if not (1 <= len(project) <= 255):
        raise ValueError("Invalid project name length.")
    if not HARBOR_PROJECT_NAME_PATTERN.match(project):
        raise ValueError("Invalid project name format.")


class AllowedGroupsModel(BaseFieldModel):
    add: list[str] = []
    remove: list[str] = []


class ContainerRegistryModel(BackendAISchema):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    url: str | None = None
    registry_name: str | None = None
    type: ContainerRegistryType | None = None
    project: str | None = None
    username: str | None = None
    password: str | None = None
    ssl_verify: bool | None = None
    is_global: bool | None = None
    extra: dict[str, Any] | None = None


class PatchContainerRegistryRequestModel(ContainerRegistryModel, BaseRequestModel):
    allowed_groups: AllowedGroupsModel | None = None


class PatchContainerRegistryResponseModel(ContainerRegistryModel, BaseResponseModel):
    pass


class CreateContainerRegistryRequestModel(BaseRequestModel):
    url: str
    registry_name: str
    type: ContainerRegistryType
    project: str | None = None
    username: str | None = None
    password: str | None = None
    ssl_verify: bool | None = None
    is_global: bool | None = None
    extra: dict[str, Any] | None = None
    allowed_groups: AllowedGroupsModel | None = None


class ListContainerRegistriesResponseModel(BaseResponseModel):
    items: list[ContainerRegistryModel]


class ImageOperationRequestModel(BaseRequestModel):
    registry: str
    project: str | None = None
