from pydantic import BaseModel, ConfigDict


class QueryTimeRange(BaseModel):
    """Time range parameters for a Prometheus query."""

    model_config = ConfigDict(frozen=True)

    start: str
    end: str
    step: str
