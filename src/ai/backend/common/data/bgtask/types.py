from pydantic import Field

from ai.backend.common.types import BackendAISchema


class BgTaskProgressData(BackendAISchema):
    current: int = Field(
        default=0,
        description="Current progress of the scan operation, expressed as a percentage.",
        examples=[0, 50, 100],
    )
    total: int = Field(
        default=0,
        description="Total number of items to be scanned, used to calculate progress.",
        examples=[100, 200, 0],
    )
