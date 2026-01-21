from pydantic import BaseModel, ConfigDict

from .logical_volume import LogicalVolume
from .uoid import UOID


class StorageVolume(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    logicalVolume: LogicalVolume
    storageVolumeState: str
    uri: str
