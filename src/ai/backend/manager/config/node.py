# TODO: Make this more precise type
from pydantic import BaseModel, ConfigDict, Field

from ai.backend.manager.config.shared import RedisConfig


class AgentsConfig(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )


class NodesConfig(BaseModel):
    manager: dict[str, str] = Field(
        default_factory=dict,
        description="""
        """,
        examples=[{"instance-id": "up"}],
    )
    redis: RedisConfig = Field(
        default_factory=RedisConfig,
        description="""
        """,
    )
    agents: AgentsConfig = Field(
        default_factory=AgentsConfig,
        description="""
        Agent configuration settings.
        Controls how agents are managed and monitored.
        """,
    )
