from pydantic import BaseModel, Field

from ...api_handlers import BaseResponseModel
from .field import VFolderItemField


class VFolderCreateResponse(BaseResponseModel):
    item: VFolderItemField


class VFolderListResponse(BaseResponseModel):
    items: list[VFolderItemField] = Field(default_factory=list)


class ActionTypeVariant(BaseModel):
    entity_type: str = Field(description="Entity type of the AuditLog")
    action_types: list[str] = Field(description="Possible Action types of the AuditLog")


class AuditLogSchemaResponseModel(BaseResponseModel):
    status_variants: list[str] = Field(description="Possible Status variants of the AuditLog")
    entity_type_variants: list[str] = Field(
        description="Possible Entity type variants of the AuditLog"
    )
    action_type_variants: list[ActionTypeVariant] = Field(
        description="Possible Action type variants of the AuditLog"
    )
