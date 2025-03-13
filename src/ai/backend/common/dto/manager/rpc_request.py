from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class PurgeImagesReq(BaseRequestModel):
    images: list[str] = Field(
        description="List of image names to be purged",
    )
    # TODO: Add proper description
    force: bool = Field(
        description="Force purge the images",
        default=False,
    )
    noprune: bool = Field(
        description="Do not prune the images",
        default=False,
    )
