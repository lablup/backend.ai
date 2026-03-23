"""
Shared types for session DTOs.

Includes creation config models (V1-V7) and their template variants,
resource options, and mount option types.
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from pydantic import AliasChoices, ConfigDict, Field, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

from ai.backend.common.api_handlers import BaseFieldModel
from ai.backend.common.types import BinarySizeField, MountPermission, MountTypes

__all__ = (
    # Annotated types
    "TimeoutSeconds",
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


class _TimeoutSecondsPydanticAnnotation:
    """Pydantic annotated type that accepts int | float | str and returns int seconds.

    Supported string formats:
    - Numeric string: "300" → 300
    - Duration suffixes: "30s", "5m", "1h", "2d", "1w"

    Not supported: "yr" / "mo" (relativedelta) — raises ValueError.
    Negative values are rejected.
    """

    @classmethod
    def timeout_seconds_validator(cls, value: int | float | str) -> int:
        if not isinstance(value, (int, float, str)):
            raise ValueError("value must be a number or string")
        if isinstance(value, (int, float)):
            result = int(value)
            if result < 0:
                raise ValueError("value must be positive")
            return result
        if len(value) == 0:
            raise ValueError("value must not be empty")

        unit = value[-1]
        if unit.isdigit():
            # Plain numeric string like "300"
            try:
                result = int(float(value))
            except ValueError as e:
                raise ValueError(f"invalid numeric literal: {value}") from e
            if result < 0:
                raise ValueError("value must be positive")
            return result
        if value[-2:].isalpha():
            # Two-char suffix like "yr" or "mo"
            suffix = value[-2:]
            if suffix in ("yr", "mo"):
                raise ValueError(f"duration unit '{suffix}' is not supported for timeout seconds")
            raise ValueError(f"unknown duration unit: {suffix!r}")
        # Single-char suffix
        try:
            t = float(value[:-1])
        except ValueError as e:
            raise ValueError(f"invalid numeric literal: {value[:-1]!r}") from e
        if t < 0:
            raise ValueError("value must be positive")
        match unit:
            case "w":
                return int(t * 7 * 24 * 3600)
            case "d":
                return int(t * 24 * 3600)
            case "h":
                return int(t * 3600)
            case "m":
                return int(t * 60)
            case "s":
                return int(t)
            case _:
                raise ValueError(f"unknown duration unit: {unit!r}")

    @classmethod
    def timeout_seconds_serializer(cls, value: int) -> int:
        return value

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        schema = core_schema.chain_schema([
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.float_schema(),
                core_schema.str_schema(),
            ]),
            core_schema.no_info_plain_validator_function(cls.timeout_seconds_validator),
        ])

        return core_schema.json_or_python_schema(
            json_schema=schema,
            python_schema=schema,
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls.timeout_seconds_serializer
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.int_schema())


TimeoutSeconds = Annotated[int, _TimeoutSecondsPydanticAnnotation]
"""Timeout in seconds. Accepts int, float (truncated to int), or duration strings like '30s', '5m', '1h', '2d', '1w'."""


class ResourceOpts(BaseFieldModel):
    """Pydantic equivalent of ``resource_opts_iv``."""

    shmem: BinarySizeField | None = None
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
    instance_memory: BinarySizeField | None = Field(
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
    """Template variant of V3 — all fields default to ``None`` (unset).

    Note: The field set is intentionally identical to :class:`CreationConfigV3`.
    In the original Trafaret schema the only difference is that template variants
    use ``default=undefined`` with an ``UndefChecker`` wrapper, whereas the
    non-template version uses ``default=None``.  In the Pydantic representation
    both collapse to ``Optional`` fields with ``None`` defaults, making the two
    classes structurally identical.  They are kept as separate types so that
    handler code can distinguish between direct creation and template-based
    creation at the type level.
    """

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
