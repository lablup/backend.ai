"""
Path parameter DTOs for domain REST API endpoints.
"""

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class GetDomainPathParam(BaseRequestModel):
    """Path parameter for getting a domain."""

    domain_name: str = Field(description="The domain name to retrieve")


class UpdateDomainPathParam(BaseRequestModel):
    """Path parameter for updating a domain."""

    domain_name: str = Field(description="The domain name to update")
