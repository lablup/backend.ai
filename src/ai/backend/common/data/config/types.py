from dataclasses import dataclass

from ai.backend.common.typed_validators import HostPortPair


@dataclass
class EtcdConfigData:
    namespace: str
    addrs: list[HostPortPair]
    user: str | None
    password: str | None
    keep_alive_interval: float
    keep_alive_timeout: float
