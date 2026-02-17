from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class GetKeyPairPathParam(BaseRequestModel):
    access_key: str = Field(description="The access key of the keypair to retrieve")


class UpdateKeyPairPathParam(BaseRequestModel):
    access_key: str = Field(description="The access key of the keypair to update")


class ActivateKeyPairPathParam(BaseRequestModel):
    access_key: str = Field(description="The access key of the keypair to activate")


class DeactivateKeyPairPathParam(BaseRequestModel):
    access_key: str = Field(description="The access key of the keypair to deactivate")
