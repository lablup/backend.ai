from dataclasses import dataclass

from ai.backend.common.types import HostPortPair


@dataclass(frozen=True)
class SentinelMaster:
    address: HostPortPair
    config_epoch: int


@dataclass(frozen=True)
class SentinelConnectionConfig:
    password: str | None = None
    use_tls: bool = False
    tls_skip_verify: bool = False
