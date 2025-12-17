import enum

from pydantic import BaseModel, ConfigDict

from .address import IPAddress
from .uoid import UOID


class NodeMode(enum.StrEnum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"
    DISABLED = "DISABLED"
    UPDATE = "UPDATE"


class NodeType(enum.StrEnum):
    PD = "PD"
    NETAPP_CMODE = "NETAPP_CMODE"
    NETAPP_7MODE = "NETAPP_7MODE"
    NETAPP_CLOUD = "NETAPP_CLOUD"
    EMC_ISILON = "EMC_ISILON"
    EMC_VNX = "EMC_VNX"
    EMC_UNITY = "EMC_UNITY"
    GOOGLE_CLOUD_FILESTORE = "GOOGLE_CLOUD_FILESTORE"
    QUMULO = "QUMULO"
    ROZOFS = "ROZOFS"
    ROZOFS_HS = "ROZOFS_HS"
    SOFTNAS_CLOUD = "SOFTNAS_CLOUD"
    WINDOWS_FILE_SERVER = "WINDOWS_FILE_SERVER"
    DELL_ENAS = "DELL_ENAS"
    PURE_FB = "PURE_FB"
    VAST = "VAST"
    WEKA = "WEKA"
    NETAPP_FSX = "NETAPP_FSX"
    AMAZON_S3 = "AMAZON_S3"
    ACTIVE_SCALE_S3 = "ACTIVE_SCALE_S3"
    IBM_S3 = "IBM_S3"
    CLOUDIAN_S3 = "CLOUDIAN_S3"
    ECS_S3 = "ECS_S3"
    GENERIC_S3 = "GENERIC_S3"
    GOOGLE_S3 = "GOOGLE_S3"
    SCALITY_S3 = "SCALITY_S3"
    STORAGE_GRID_S3 = "STORAGE_GRID_S3"
    SWIFT = "SWIFT"
    AZURE = "AZURE"
    GOOGLE_CLOUD = "GOOGLE_CLOUD"
    HCP_S3 = "HCP_S3"
    ATMOS = "ATMOS"
    WASABI_S3 = "WASABI_S3"
    NETAPP_S3 = "NETAPP_S3"
    MCAFEE_AV = "MCAFEE_AV"
    CLAM_AV = "CLAM_AV"
    SNOWFLAKE = "SNOWFLAKE"
    INTERNAL_S3 = "INTERNAL_S3"
    ALCHEMI = "ALCHEMI"
    PURE_FB_S3 = "PURE_FB_S3"
    SEAGATE_LYVE_S3 = "SEAGATE_LYVE_S3"
    CARINGO_SWARM_S3 = "CARINGO_SWARM_S3"
    ISILON_S3 = "ISILON_S3"
    BACKBLAZE_S3 = "BACKBLAZE_S3"
    HAMMERSPACE_S3 = "HAMMERSPACE_S3"
    OTHER = "OTHER"
    MOVER_EXT = "MOVER_EXT"


class ProductionNodeType(enum.StrEnum):
    ANVIL = "ANVIL"
    DSX = "DSX"


class Node(BaseModel):
    model_config = ConfigDict(extra="allow")

    uoid: UOID
    name: str
    internalId: int
    mgmtIpAddress: IPAddress
    nodeMode: NodeMode
    nodeType: NodeType
    productNodeType: ProductionNodeType
