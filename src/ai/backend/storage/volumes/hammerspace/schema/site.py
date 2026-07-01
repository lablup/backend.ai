import enum

from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema

from .uoid import UOID


class SiteType(enum.StrEnum):
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"


class Site(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    created: int  # timestamp
    modified: int  # timestamp
    name: str
    type: SiteType
