from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema

from .logical_volume import LogicalVolume
from .uoid import UOID


class StorageVolume(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    logicalVolume: LogicalVolume
    storageVolumeState: str
    uri: str
