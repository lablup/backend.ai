import uuid

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class GetNetworkPathParam(BaseRequestModel):
    network_id: uuid.UUID = Field(description="The network ID to retrieve")


class UpdateNetworkPathParam(BaseRequestModel):
    network_id: uuid.UUID = Field(description="The network ID to update")
