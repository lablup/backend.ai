"""
Shared types for session DTOs.

Includes creation config models (V1-V7) and their template variants,
resource options, and mount option types.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import AliasChoices, ConfigDict, Field

from ai.backend.common.api_handlers import BaseFieldModel
from ai.backend.common.types import BinarySize, MountPermission, MountTypes

__all__ = (
    # Shared field models
    "ResourceOpts",
    "MountOption",
    # Creation configs
    "CreationConfigV1",
    "CreationConfigV2",
    "CreationConfigV3",
    "CreationConfigV3Template",
    "CreationConfigV4",
    "CreationConfigV4Template",
    "CreationConfigV5",
    "CreationConfigV5Template",
    "CreationConfigV6",
    "CreationConfigV6Template",
    "CreationConfigV7",
)


class ResourceOpts(BaseFieldModel):
    """Pydantic equivalent of ``resource_opts_iv``."""

    shmem: BinarySize | None = None
    allow_fractional_resource_fragmentation: bool | None = None
    model_config = ConfigDict(extra="allow")


class MountOption(BaseFieldModel):
    """Per-mount option used inside ``mount_options`` mapping."""

    type: MountTypes = MountTypes.BIND
    permission: MountPermission | None = Field(
        default=None,
        validation_alias=AliasChoices("permission", "perm"),
    )
    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Creation configs — progressive API version evolution
# ---------------------------------------------------------------------------


class CreationConfigV1(BaseFieldModel):
    """API v1-v2 creation config."""

    mounts: list[str] | None = None
    environ: dict[str, str] | None = None
    cluster_size: int | None = Field(
        default=None,
        ge=1,
        validation_alias=AliasChoices("cluster_size", "clusterSize"),
    )


class CreationConfigV2(BaseFieldModel):
    """API v2 creation config — adds per-instance resource hints."""

    mounts: list[str] | None = None
    environ: dict[str, str] | None = None
    cluster_size: int | None = Field(
        default=None,
        ge=1,
        validation_alias=AliasChoices("cluster_size", "clusterSize"),
    )
    instance_memory: BinarySize | None = Field(
        default=None,
        validation_alias=AliasChoices("instance_memory", "instanceMemory"),
    )
    instance_cores: int | None = Field(
        default=None,
        validation_alias=AliasChoices("instance_cores", "instanceCores"),
    )
    instance_gpus: float | None = Field(
        default=None,
        validation_alias=AliasChoices("instance_gpus", "instanceGPUs"),
    )
    instance_tpus: int | None = Field(
        default=None,
        validation_alias=AliasChoices("instance_tpus", "instanceTPUs"),
    )


class CreationConfigV3(BaseFieldModel):
    """API v3 creation config — resource slots model."""

    mounts: list[str] | None = None
    environ: dict[str, str] | None = None
    cluster_size: int | None = Field(
        default=None,
        ge=1,
        validation_alias=AliasChoices("cluster_size", "clusterSize"),
    )
    scaling_group: str | None = Field(
        default=None,
        validation_alias=AliasChoices("scaling_group", "scalingGroup"),
    )
    resources: dict[str, object] | None = None
    resource_opts: ResourceOpts | None = Field(
        default=None,
        validation_alias=AliasChoices("resource_opts", "resourceOpts"),
    )


class CreationConfigV3Template(BaseFieldModel):
    """Template variant of V3 — all fields default to ``None`` (unset)."""

    mounts: list[str] | None = None
    environ: dict[str, str] | None = None
    cluster_size: int | None = Field(
        default=None,
        ge=1,
        validation_alias=AliasChoices("cluster_size", "clusterSize"),
    )
    scaling_group: str | None = Field(
        default=None,
        validation_alias=AliasChoices("scaling_group", "scalingGroup"),
    )
    resources: dict[str, object] | None = None
    resource_opts: ResourceOpts | None = Field(
        default=None,
        validation_alias=AliasChoices("resource_opts", "resourceOpts"),
    )


class CreationConfigV4(BaseFieldModel):
    """API v4 creation config — adds mount_map, preopen_ports."""

    mounts: list[str] | None = None
    mount_map: dict[str, str] | None = Field(
        default=None,
        validation_alias=AliasChoices("mount_map", "mountMap"),
    )
    environ: dict[str, str] | None = None
    cluster_size: int | None = Field(
        default=None,
        ge=1,
        validation_alias=AliasChoices("cluster_size", "clusterSize"),
    )
    scaling_group: str | None = Field(
        default=None,
        validation_alias=AliasChoices("scaling_group", "scalingGroup"),
    )
    resources: dict[str, object] | None = None
    resource_opts: ResourceOpts | None = Field(
        default=None,
        validation_alias=AliasChoices("resource_opts", "resourceOpts"),
    )
    preopen_ports: list[int] | None = Field(
        default=None,
        validation_alias=AliasChoices("preopen_ports", "preopenPorts"),
    )


class CreationConfigV4Template(BaseFieldModel):
    """Template variant of V4."""

    mounts: list[str] | None = None
    mount_map: dict[str, str] | None = Field(
        default=None,
        validation_alias=AliasChoices("mount_map", "mountMap"),
    )
    environ: dict[str, str] | None = None
    cluster_size: int | None = Field(
        default=None,
        ge=1,
        validation_alias=AliasChoices("cluster_size", "clusterSize"),
    )
    scaling_group: str | None = Field(
        default=None,
        validation_alias=AliasChoices("scaling_group", "scalingGroup"),
    )
    resources: dict[str, object] | None = None
    resource_opts: ResourceOpts | None = Field(
        default=None,
        validation_alias=AliasChoices("resource_opts", "resourceOpts"),
    )


class CreationConfigV5(BaseFieldModel):
    """API v5 creation config — adds mount_options, agent_list."""

    mounts: list[str] | None = None
    mount_map: dict[str, str] | None = Field(
        default=None,
        validation_alias=AliasChoices("mount_map", "mountMap"),
    )
    mount_options: dict[str, MountOption] | None = Field(
        default=None,
        validation_alias=AliasChoices("mount_options", "mountOptions"),
    )
    environ: dict[str, str] | None = None
    scaling_group: str | None = Field(
        default=None,
        validation_alias=AliasChoices("scaling_group", "scalingGroup"),
    )
    resources: dict[str, object] | None = None
    resource_opts: ResourceOpts | None = Field(
        default=None,
        validation_alias=AliasChoices("resource_opts", "resourceOpts"),
    )
    preopen_ports: list[int] | None = Field(
        default=None,
        validation_alias=AliasChoices("preopen_ports", "preopenPorts"),
    )
    agent_list: list[str] | None = Field(
        default=None,
        validation_alias=AliasChoices("agent_list", "agentList"),
    )


class CreationConfigV5Template(BaseFieldModel):
    """Template variant of V5."""

    mounts: list[str] | None = None
    mount_map: dict[str, str] | None = Field(
        default=None,
        validation_alias=AliasChoices("mount_map", "mountMap"),
    )
    environ: dict[str, str] | None = None
    scaling_group: str | None = Field(
        default=None,
        validation_alias=AliasChoices("scaling_group", "scalingGroup"),
    )
    resources: dict[str, object] | None = None
    resource_opts: ResourceOpts | None = Field(
        default=None,
        validation_alias=AliasChoices("resource_opts", "resourceOpts"),
    )


class CreationConfigV6(BaseFieldModel):
    """API v6 creation config — adds attach_network."""

    mounts: list[str] | None = None
    mount_map: dict[str, str] | None = Field(
        default=None,
        validation_alias=AliasChoices("mount_map", "mountMap"),
    )
    mount_options: dict[str, MountOption] | None = Field(
        default=None,
        validation_alias=AliasChoices("mount_options", "mountOptions"),
    )
    environ: dict[str, str] | None = None
    scaling_group: str | None = Field(
        default=None,
        validation_alias=AliasChoices("scaling_group", "scalingGroup"),
    )
    resources: dict[str, object] | None = None
    resource_opts: ResourceOpts | None = Field(
        default=None,
        validation_alias=AliasChoices("resource_opts", "resourceOpts"),
    )
    preopen_ports: list[int] | None = Field(
        default=None,
        validation_alias=AliasChoices("preopen_ports", "preopenPorts"),
    )
    agent_list: list[str] | None = Field(
        default=None,
        validation_alias=AliasChoices("agent_list", "agentList"),
    )
    attach_network: UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("attach_network", "attachNetwork"),
    )


class CreationConfigV6Template(BaseFieldModel):
    """Template variant of V6."""

    mounts: list[str] | None = None
    mount_map: dict[str, str] | None = Field(
        default=None,
        validation_alias=AliasChoices("mount_map", "mountMap"),
    )
    environ: dict[str, str] | None = None
    scaling_group: str | None = Field(
        default=None,
        validation_alias=AliasChoices("scaling_group", "scalingGroup"),
    )
    resources: dict[str, object] | None = None
    resource_opts: ResourceOpts | None = Field(
        default=None,
        validation_alias=AliasChoices("resource_opts", "resourceOpts"),
    )
    attach_network: UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("attach_network", "attachNetwork"),
    )


class CreationConfigV7(BaseFieldModel):
    """API v7 creation config — adds mount_ids/mount_id_map, deprecates mounts/mount_map."""

    mounts: list[str] | None = None
    mount_map: dict[str, str] | None = Field(
        default=None,
        validation_alias=AliasChoices("mount_map", "mountMap"),
    )
    mount_ids: list[UUID] | None = None
    mount_id_map: dict[UUID, str] | None = Field(
        default=None,
        validation_alias=AliasChoices("mount_id_map", "mountIdMap"),
    )
    mount_options: dict[str, MountOption] | None = Field(
        default=None,
        validation_alias=AliasChoices("mount_options", "mountOptions"),
    )
    environ: dict[str, str] | None = None
    scaling_group: str | None = Field(
        default=None,
        validation_alias=AliasChoices("scaling_group", "scalingGroup"),
    )
    resources: dict[str, object] | None = None
    resource_opts: ResourceOpts | None = Field(
        default=None,
        validation_alias=AliasChoices("resource_opts", "resourceOpts"),
    )
    preopen_ports: list[int] | None = Field(
        default=None,
        validation_alias=AliasChoices("preopen_ports", "preopenPorts"),
    )
    agent_list: list[str] | None = Field(
        default=None,
        validation_alias=AliasChoices("agent_list", "agentList"),
    )
    attach_network: UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("attach_network", "attachNetwork"),
    )
