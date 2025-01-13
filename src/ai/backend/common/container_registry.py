import enum
import uuid
from typing import Any, Optional

from pydantic import BaseModel


class ContainerRegistryType(enum.StrEnum):
    DOCKER = "docker"
    HARBOR = "harbor"
    HARBOR2 = "harbor2"
    GITHUB = "github"
    GITLAB = "gitlab"
    ECR = "ecr"
    ECR_PUB = "ecr-public"
    LOCAL = "local"


class AllowedGroupsModel(BaseModel):
    add: list[str] = []
    remove: list[str] = []


class ContainerRegistryRowModel(BaseModel):
    id: Optional[uuid.UUID] = None
    url: Optional[str] = None
    registry_name: Optional[str] = None
    type: Optional[ContainerRegistryType] = None
    project: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_verify: Optional[bool] = None
    is_global: Optional[bool] = None
    extra: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


class PatchContainerRegistryRequestModel(ContainerRegistryRowModel):
    allowed_groups: Optional[AllowedGroupsModel] = None


class PatchContainerRegistryResponseModel(ContainerRegistryRowModel):
    pass
