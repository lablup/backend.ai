import enum

from pydantic import BaseModel, ConfigDict

from .address import IPAddress, QualifiedAddress
from .capacity import Capacity
from .fstype import FsType
from .node import Node
from .service_state import ServiceState
from .uoid import UOID


class UsageType(enum.StrEnum):
    DS = "DS"
    OTHER = "OTHER"


class LogicalVolume(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    modified: int  # timestamp
    quotaIsSet: bool
    serviceState: ServiceState
    addresses: list[QualifiedAddress]
    exportPath: str  # NFS export path
    aliases: list[str]
    fsType: FsType
    capacity: Capacity
    ipAddresses: list[IPAddress]
    node: Node
    usageType: UsageType
