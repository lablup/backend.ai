from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class ImageCommitRegistryReq(BaseRequestModel):
    """The registry and the project a project commits its session images into.

    ``project`` is absent for a registry that has none: only Harbor requires one.
    """

    registry: str = Field(min_length=1)
    project: str | None
