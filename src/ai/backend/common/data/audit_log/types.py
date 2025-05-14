from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel


class ActionType(BaseModel):
    entity_type: str = Field(description="Entity type of the AuditLog")
    action_types: list[str] = Field(description="Action types of the AuditLog")


class AuditLogSchemaResponseModel(BaseResponseModel):
    status_variants: list[str] = Field(description="Possible Status variants of the AuditLog")
    entity_type_variants: list[str] = Field(
        description="Possible Entity type variants of the AuditLog"
    )
    action_types: list[ActionType] = Field(description="Possible Action types of the AuditLog")
