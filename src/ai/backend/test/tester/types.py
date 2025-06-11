from typing import Literal

from pydantic import BaseModel, Field

from ai.backend.client.config import APIConfig


class APIConfigModel(BaseModel):
    endpoint: str = Field(
        description="The API endpoint for the test.",
        examples=["http://127.0.0.1:8091/"],
    )
    endpoint_type: Literal["api", "session"] = Field(
        description="The type of the API endpoint.",
        examples=["api", "session"],
        alias="endpoint-type",
    )
    access_key: str = Field(
        description="The access key for the API.", examples=["some-access-key"], alias="access-key"
    )
    secret_key: str = Field(
        description="The secret key for the API.", examples=["some-secret-key"], alias="secret-key"
    )

    def to_api_config(self) -> APIConfig:
        return APIConfig(
            endpoint=self.endpoint,
            endpoint_type=self.endpoint_type,
            access_key=self.access_key,
            secret_key=self.secret_key,
        )


class TesterConfigModel(BaseModel):
    api_configs: dict[str, APIConfigModel] = Field(
        default_factory=dict,
        description="Dictionary of API configurations for the test.",
        validation_alias="api-configs",
    )
