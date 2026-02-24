"""
Path parameter DTOs for resource policy REST API endpoints.
"""

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class GetResourcePolicyPathParam(BaseRequestModel):
    """Path parameter for getting a resource policy."""

    policy_name: str = Field(description="The resource policy name to retrieve")


class UpdateResourcePolicyPathParam(BaseRequestModel):
    """Path parameter for updating a resource policy."""

    policy_name: str = Field(description="The resource policy name to update")
