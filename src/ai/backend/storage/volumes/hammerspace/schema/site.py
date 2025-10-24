import enum

from pydantic import BaseModel, ConfigDict

from .uoid import UOID


class SiteType(enum.StrEnum):
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"


class Site(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    created: int  # timestamp
    modified: int  # timestamp
    name: str
    type: SiteType
