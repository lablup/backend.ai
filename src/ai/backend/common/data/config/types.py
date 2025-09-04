from dataclasses import dataclass
from typing import Annotated, Optional

from pydantic import BaseModel, Field

from ai.backend.common.typed_validators import HostPortPair


@dataclass
class EtcdConfigData:
    namespace: str
    addrs: list[HostPortPair]
    user: Optional[str]
    password: Optional[str]


class HealthCheckConfig(BaseModel):
    """
    Health check configuration matching model-definition.yaml schema
    """

    interval: Annotated[float, Field(default=10.0, ge=0)] = 10.0
    path: str
    max_retries: Annotated[int, Field(default=10, ge=1)] = 10
    max_wait_time: Annotated[float, Field(default=15.0, ge=0)] = 15.0
    expected_status_code: Annotated[int, Field(default=200, ge=100, le=599)] = 200
