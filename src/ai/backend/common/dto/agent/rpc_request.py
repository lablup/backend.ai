from pydantic import Field

from ...api_handlers import BaseRequestModel


class PurgeImagesReq(BaseRequestModel):
    images: list[str] = Field(
        description="List of image canonical names to be purged",
    )
    force: bool = Field(
        description="Remove the images even if it is being used by stopped containers or has other tags",
        default=False,
    )
    noprune: bool = Field(
        description="Don't delete untagged parent images",
        default=False,
    )
