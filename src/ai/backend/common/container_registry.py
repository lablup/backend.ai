import enum
import re
import uuid
from dataclasses import dataclass
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


_HARBOR_TYPES = (ContainerRegistryType.HARBOR, ContainerRegistryType.HARBOR2)
_HARBOR_PROJECT_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")


@dataclass(frozen=True)
class ContainerRegistryValidator:
    """Checks a registry's address and Harbor project. Raises ValueError, so a
    pydantic validator can call it as it is."""

    url: str | None
    type: ContainerRegistryType | None
    project: str | None

    def validate(self) -> None:
        """A whole registry: the address must parse, and a Harbor registry must name
        a well-formed project."""
        if self.url is None:
            raise ValueError("URL is required.")
        self._validate_url(self.url)
        if self.type not in _HARBOR_TYPES:
            return
        if self.project is None:
            raise ValueError("Project name is required for Harbor.")
        self._validate_project(self.project)

    def validate_patch(self) -> None:
        """A partial update, judged on its own: the address when given, the project
        only when the same patch names a Harbor type."""
        if self.url is not None:
            self._validate_url(self.url)
        if self.type in _HARBOR_TYPES and self.project is not None:
            self._validate_project(self.project)

    @staticmethod
    def _validate_url(url: str) -> None:
        """A bare host is read as http."""
        candidate = url if url.startswith(("http://", "https://")) else f"http://{url}"
        try:
            parsed = urlparse(candidate)
        except ValueError:
            raise ValueError(f"Invalid URL format: {url}") from None
        if not (parsed.scheme and parsed.netloc):
            raise ValueError(f"Invalid URL format: {url}")

    @staticmethod
    def _validate_project(project: str) -> None:
        if not (1 <= len(project) <= 255):
            raise ValueError("Invalid project name length.")
        if not _HARBOR_PROJECT_NAME_PATTERN.match(project):
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
