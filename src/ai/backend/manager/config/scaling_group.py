# TODO: Make this more precise type
from pydantic import BaseModel, ConfigDict


class ScalingGroupConfig(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
