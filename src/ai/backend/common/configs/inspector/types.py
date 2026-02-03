from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ai.backend.common.meta import CompositeType, ConfigExample

__all__ = (
    "FieldTypeInfo",
    "FieldDocumentation",
    "FieldSchema",
)


@dataclass(frozen=True)
class FieldTypeInfo:
    """Type information for a configuration field.

    Captures the runtime type characteristics of a field including
    whether it's required, has defaults, and whether it contains secrets.
    """

    type_name: str
    """The name of the type (e.g., 'str', 'int', 'DatabaseConfig')."""

    default: Any
    """The default value if the field has one, None otherwise.
    For required fields without defaults, this will be the sentinel PydanticUndefined."""

    required: bool
    """Whether the field is required (no default value)."""

    secret: bool
    """Whether this field contains sensitive information that should be masked."""

    composite_type: CompositeType | None = None
    """Type of composite field structure, if this is a composite field.

    - None: Simple field (not composite)
    - FIELD: Single nested object (e.g., DatabaseConfig)
    - DICT: Dictionary with string keys (e.g., dict[str, VolumeConfig])
    - LIST: List of objects (e.g., list[EndpointConfig])

    Used by generators to produce proper output format for nested structures.
    """


@dataclass(frozen=True)
class FieldDocumentation:
    """Documentation metadata for a configuration field.

    Contains human-readable documentation extracted from BackendAIConfigMeta,
    including versioning information for tracking field evolution.
    """

    description: str
    """Human-readable description of the field's purpose and usage."""

    example: ConfigExample | None
    """Environment-specific example values for LOCAL and PROD environments."""

    added_version: str
    """Version when this field was first introduced (e.g., '25.1.0')."""

    deprecated_version: str | None = None
    """Version when this field was deprecated, if applicable."""

    deprecation_hint: str | None = None
    """Migration guidance for deprecated fields."""


@dataclass(frozen=True)
class FieldSchema:
    """Complete schema information for a configuration field.

    Combines type information, documentation, and optional child schemas
    for composite fields into a unified structure.
    """

    key: str
    """The TOML key name (from serialization_alias or field name)."""

    type_info: FieldTypeInfo
    """Type and default value information."""

    doc: FieldDocumentation
    """Documentation and versioning information."""

    children: Mapping[str, FieldSchema] | None = None
    """Child field schemas for composite types, None for leaf fields."""
