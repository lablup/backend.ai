from dataclasses import dataclass
from typing import Optional

from ai.backend.common.typed_validators import HostPortPair


@dataclass
class EtcdConfigData:
    namespace: str
    addrs: list[HostPortPair]
    user: Optional[str]
    password: Optional[str]
