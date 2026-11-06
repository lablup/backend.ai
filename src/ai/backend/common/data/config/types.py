from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.typed_validators import HostPortPair


@dataclass
class EtcdTLSConfigData:
    ca_cert: Path
    client_cert: Path | None
    client_key: Path | None
    handshake_timeout: float


@dataclass
class EtcdConfigData:
    namespace: str
    addrs: list[HostPortPair]
    user: str | None
    password: str | None
    keep_alive_interval: float
    keep_alive_timeout: float
    tls: EtcdTLSConfigData | None
