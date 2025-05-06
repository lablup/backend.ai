from typing import Any, Optional

from pydantic import BaseModel, Field

from ai.backend.common.typed_validators import CommaSeparatedStrList


class VolumeTypeConfig(BaseModel):
    user: Optional[dict[str, Any] | str] = Field(
        default=None,
        description="""
        User VFolder type configuration.
        When present, enables user-owned virtual folders.
        Standard folder type for individual users.
        """,
    )
    group: Optional[dict[str, Any] | str] = Field(
        default=None,
        description="""
        Group VFolder type configuration.
        When present, enables group-owned virtual folders.
        Used for sharing files within a group of users.
        """,
    )


class VolumeProxyConfig(BaseModel):
    client_api: str = Field(
        description="""
        Client-facing API endpoint URL of the volume proxy.
        Used by clients to access virtual folder contents.
        Should include protocol, host and port.
        """,
        examples=["http://localhost:6021", "https://proxy1.example.com:6021"],
    )
    manager_api: str = Field(
        description="""
        Manager-facing API endpoint URL of the volume proxy.
        Used by manager to communicate with the volume proxy.
        Should include protocol, host and port.
        """,
        examples=["http://localhost:6022", "https://proxy1.example.com:6022"],
    )
    secret: str = Field(
        description="""
        Secret key for authenticating with the volume proxy manager API.
        Must match the secret configured on the volume proxy.
        Should be kept secure and not exposed to clients.
        """,
        examples=["some-secret-key"],
    )
    ssl_verify: bool = Field(
        default=True,
        description="""
        Whether to verify SSL certificates when connecting to the volume proxy.
        Should be enabled in production for security.
        Can be disabled for testing with self-signed certificates.
        """,
        examples=[True, False],
    )
    sftp_scaling_groups: Optional[CommaSeparatedStrList] = Field(
        default=None,
        description="""
        List of SFTP scaling groups that the volume is mapped to.
        Controls which scaling groups can create SFTP sessions for this volume.
        """,
        examples=[None, ["group-1", "group-2"]],
    )


class VolumeConfig(BaseModel):
    types: VolumeTypeConfig = Field(
        default_factory=lambda: VolumeTypeConfig(user={}),
        description="""
        Defines which types of virtual folders are enabled.
        Contains configuration for user and group folders.
        """,
        alias="_types",
    )
    default_host: str = Field(
        description="""
        Default volume host for new virtual folders.
        Format is "proxy_name:volume_name".
        Used when user doesn't explicitly specify a host.
        """,
        examples=["local:default", "nas:main-volume"],
    )
    exposed_volume_info: CommaSeparatedStrList = Field(
        default=CommaSeparatedStrList(["percentage"]),
        description="""
        Controls what volume information is exposed to users.
        Options include "percentage" for disk usage percentage.
        """,
        examples=[["percentage"], ["percentage", "bytes"]],
    )
    proxies: dict[str, VolumeProxyConfig] = Field(
        description="""
        Mapping of volume proxy configurations.
        Each key is a proxy name used in volume host references.
        """,
        examples=[
            {
                "local": {
                    "client_api": "http://localhost:6021",
                    "manager_api": "http://localhost:6022",
                    "secret": "some-secret",
                    "ssl_verify": True,
                }
            }
        ],
    )
