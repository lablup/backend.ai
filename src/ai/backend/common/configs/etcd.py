from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.data.config.types import EtcdConfigData
from ai.backend.common.meta import BackendAIConfigMeta, ConfigExample
from ai.backend.common.typed_validators import HostPortPair

__all__ = ("EtcdConfig",)


class EtcdConfig(BaseConfigSchema):
    """Configuration for etcd connection.

    etcd is used as the distributed key-value store for Backend.AI cluster
    configuration and coordination.
    """

    namespace: Annotated[
        str,
        Field(default="local"),
        BackendAIConfigMeta(
            description=(
                "Namespace prefix for etcd keys used by Backend.AI. "
                "Allows multiple Backend.AI clusters to share the same etcd cluster. "
                "All Backend.AI related keys will be stored under this namespace."
            ),
            added_version="22.03.0",
            example=ConfigExample(local="local", prod="backend"),
        ),
    ]
    addr: Annotated[
        HostPortPair | list[HostPortPair],
        Field(default_factory=lambda: HostPortPair(host="127.0.0.1", port=2379)),
        BackendAIConfigMeta(
            description=(
                "Network address of the etcd server. "
                "Default is the standard etcd port on localhost. "
                "In production, should point to one or more etcd instance endpoint(s)."
            ),
            added_version="22.03.0",
            example=ConfigExample(local="127.0.0.1:2379", prod="etcd-cluster:2379"),
        ),
    ]
    user: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Username for authenticating with etcd. "
                "Optional if etcd doesn't require authentication. "
                "Should be set along with password for secure deployments."
            ),
            added_version="22.03.0",
            example=ConfigExample(local="", prod="backend"),
        ),
    ]
    password: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Password for authenticating with etcd. "
                "Should be kept secret in production environments. "
                "Set together with the user field for authentication."
            ),
            added_version="22.03.0",
            secret=True,
            example=ConfigExample(local="", prod="ETCD_PASSWORD"),
        ),
    ]
    keep_alive_interval: Annotated[
        float,
        Field(default=5.0, gt=0),
        BackendAIConfigMeta(
            description=(
                "Seconds without a frame from an etcd member before a keep-alive ping is sent "
                "on a connection with requests in flight. "
                "Must not be below the server's --grpc-keepalive-min-time (5 seconds by default)."
            ),
            added_version="26.4.16",
            example=ConfigExample(local="5.0", prod="5.0"),
        ),
    ]
    keep_alive_timeout: Annotated[
        float,
        Field(default=3.0, gt=0),
        BackendAIConfigMeta(
            description=(
                "Seconds to wait for a keep-alive ping reply before the connection to that "
                "etcd member is closed and its requests go to the other members."
            ),
            added_version="26.4.16",
            example=ConfigExample(local="3.0", prod="3.0"),
        ),
    ]

    def to_dataclass(self) -> EtcdConfigData:
        """Convert to EtcdConfigData dataclass."""
        return EtcdConfigData(
            namespace=self.namespace,
            addrs=self.addr if isinstance(self.addr, list) else [self.addr],
            user=self.user,
            password=self.password,
            keep_alive_interval=self.keep_alive_interval,
            keep_alive_timeout=self.keep_alive_timeout,
        )
