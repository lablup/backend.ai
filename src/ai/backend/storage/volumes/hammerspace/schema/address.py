from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema


class IPAddress(BackendAISchema):
    address: str  # IPv4 address
    prefixLength: int


class QualifiedAddress(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    id: int
    ip: IPAddress
    port: int
    netId: str
    nodeNum: int
    stripeClass: int
    failoverClass: int
