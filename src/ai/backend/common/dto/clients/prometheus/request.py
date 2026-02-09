from pydantic import BaseModel, ConfigDict


class QueryTimeRange(BaseModel):
    """Time range parameters for a Prometheus query."""

    start: str
    end: str
    step: str

    model_config = ConfigDict(frozen=True)
