import enum

from pydantic import BaseModel, ConfigDict

from .df_entry import DFEntry
from .objective import SimpleObjective
from .uoid import UOID


class ShareState(enum.StrEnum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    MOUNTED = "MOUNTED"
    PUBLISHED = "PUBLISHED"
    CREATED = "CREATED"
    PRE_REMOVAL = "PRE_REMOVAL"
    REMOVING = "REMOVING"
    REMOVED = "REMOVED"
    RECLAIMING = "RECLAIMING"
    REMOVE_FAILED = "REMOVE_FAILED"


class ShareLifecycle(enum.StrEnum):
    CREATING = "CREATING"
    CREATED = "CREATED"
    PRE_DELETE = "PRE_DELETE"
    DELETE_SCHEDULED = "DELETE_SCHEDULED"
    DELETING = "DELETING"
    DELETE_FAILED = "DELETE_FAILED"


class ShareObjective(BaseModel):
    model_config = ConfigDict(extra="allow")

    objective: SimpleObjective
    applicability: str
    removable: bool


class SimpleShare(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    path: str


class Share(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    modified: int  # timestamp
    totalNumberOfFiles: int
    inodes: DFEntry
    space: DFEntry
    path: str
    shareState: ShareState
    shareLifecycle: ShareLifecycle
    shareObjectives: list[ShareObjective]
