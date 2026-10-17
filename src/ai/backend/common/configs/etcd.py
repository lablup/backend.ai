from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any

from pydantic import Field, model_validator

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.data.config.types import EtcdConfigData
from ai.backend.common.meta import BackendAIConfigMeta, CompositeType, ConfigExample
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
        HostPortPair | list[HostPortPair] | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Network address of the etcd server, or a list of them. "
                "Read as addrs when addrs is not set."
            ),
            added_version="22.03.0",
            deprecated_version="26.10.0",
            deprecation_hint="Use addrs instead.",
        ),
    ]
    addrs: Annotated[
        list[HostPortPair],
        Field(default_factory=lambda: [HostPortPair(host="127.0.0.1", port=2379)], min_length=1),
        BackendAIConfigMeta(
            description=(
                "Addresses of the etcd cluster members. "
                "List every member of an etcd cluster, or a single address of a standalone server."
            ),
            added_version="26.10.0",
            composite=CompositeType.LIST,
            example=ConfigExample(local="127.0.0.1:2379", prod="etcd1.example.com:2379"),
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

    @model_validator(mode="before")
    @classmethod
    def _read_addr_as_addrs(cls, data: Any) -> Any:
        if (
            not isinstance(data, Mapping)
            or data.get("addr") is None
            or data.get("addrs") is not None
        ):
            return data
        addr = data["addr"]
        return {**data, "addrs": addr if isinstance(addr, list) else [addr]}

    def to_dataclass(self) -> EtcdConfigData:
        """Convert to EtcdConfigData dataclass."""
        return EtcdConfigData(
            namespace=self.namespace,
            addrs=self.addrs,
            user=self.user,
            password=self.password,
        )
