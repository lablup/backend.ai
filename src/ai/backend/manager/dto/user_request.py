"""
Manager-specific path parameter models for user admin REST API.
"""

import uuid

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class GetUserPathParam(BaseRequestModel):
    user_id: uuid.UUID = Field(description="The user ID to retrieve")


class UpdateUserPathParam(BaseRequestModel):
    user_id: uuid.UUID = Field(description="The user ID to update")
