from pydantic import BaseModel, ConfigDict


class IPAddress(BaseModel):
    address: str  # IPv4 address
    prefixLength: int


class QualifiedAddress(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    ip: IPAddress
    port: int
    netId: str
    nodeNum: int
    stripeClass: int
    failoverClass: int
