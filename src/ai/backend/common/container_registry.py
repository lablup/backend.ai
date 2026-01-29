import enum
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

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


class AllowedGroupsModel(BaseFieldModel):
    add: list[str] = []
    remove: list[str] = []


class ContainerRegistryModel(BaseModel):
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
