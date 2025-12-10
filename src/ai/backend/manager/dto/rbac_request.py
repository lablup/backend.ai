import uuid

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class GetRolePathParam(BaseRequestModel):
    role_id: uuid.UUID = Field(description="The role ID to retrieve")


class UpdateRolePathParam(BaseRequestModel):
    role_id: uuid.UUID = Field(description="The role ID to update")


class DeleteRolePathParam(BaseRequestModel):
    role_id: uuid.UUID = Field(description="The role ID to delete")


class SearchUsersAssignedToRolePathParam(BaseRequestModel):
    role_id: uuid.UUID = Field(description="The role ID to search assigned users for")
