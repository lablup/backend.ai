from dataclasses import dataclass
from typing import Annotated, List, Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai.backend.common.types import BinarySize


class BaseModel(PydanticBaseModel):
    """Base model for all models in this module"""

    model_config = {"arbitrary_types_allowed": True}


@dataclass
class ResponseModel:
    user_model: Optional[BaseModel] = None
    status: Annotated[int, Field(strict=True, exclude=True, ge=100, lt=600)] = 200


@dataclass
class ProcessingResponseModel(ResponseModel):
    user_model: Optional[BaseModel] = None
    status: int = 202


@dataclass
class NoContentResponseModel(ResponseModel):
    user_model: Optional[BaseModel] = None
    status: int = 204


class VolumeMetadataResponseModel(BaseModel):
    volume_id: str
    backend: str
    path: str
    fsprefix: Optional[str] = None
    capabilities: List[str]


class GetVolumeResponseModel(BaseModel):
    volumes: List[VolumeMetadataResponseModel]


class QuotaScopeResponseModel(BaseModel):
    used_bytes: Optional[int] = 0
    limit_bytes: Optional[int] = 0


class VFolderMetadataResponseModel(BaseModel):
    mount_path: str
    file_count: int
    capacity_bytes: int
    used_bytes: BinarySize
