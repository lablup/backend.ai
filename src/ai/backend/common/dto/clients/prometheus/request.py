from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema


class QueryTimeRange(BackendAISchema):
    """Time range parameters for a Prometheus query."""

    start: str
    end: str
    step: str

    model_config = ConfigDict(frozen=True)
