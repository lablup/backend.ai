from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel as PydanticBaseModel

if TYPE_CHECKING:
    from pydantic import BaseModel

__all__ = (
    "ConfigEnvironment",
    "CompositeType",
    "ConfigExample",
    "BackendAIFieldMeta",
    "BackendAIConfigMeta",
    "BackendAIAPIMeta",
    "get_field_meta",
    "get_field_type",
    "generate_example",
    "generate_composite_example",
    "generate_model_example",
)


class ConfigEnvironment(enum.StrEnum):
    """Environment type for configuration examples."""

    LOCAL = "local"
    PROD = "prod"


class CompositeType(enum.StrEnum):
    """Type of composite field structure.

    Used to indicate how nested configuration fields should be handled
    in various output formats (TOML, etcd, JSON Schema).
    """

    FIELD = "field"
    """Single nested object (e.g., DatabaseConfig)."""

    DICT = "dict"
    """Dictionary with string keys (e.g., dict[str, VolumeConfig]).
    Key type is always assumed to be str."""

    LIST = "list"
    """List of objects (e.g., list[EndpointConfig])."""


@dataclass(frozen=True)
class ConfigExample:
    """Environment-specific configuration examples.

    Provides different example values for local development and production environments.
    This helps users understand appropriate values for each environment context.
    """

    local: str
    """Example value for local development environment."""

    prod: str
    """Example value for production environment."""

    def get(self, env: ConfigEnvironment) -> str:
        """Get the example value for the specified environment."""
        match env:
            case ConfigEnvironment.LOCAL:
                return self.local
            case ConfigEnvironment.PROD:
                return self.prod


@dataclass(frozen=True)
class BackendAIFieldMeta:
    """Common field metadata for documentation and version management.

    This is the base class for all Backend.AI field metadata.
    It provides fields for documentation and version tracking that are common
    across configuration fields and API fields.
    """

    description: str
    """Human-readable description of the field's purpose and usage."""

    added_version: str
    """Version when this field was first introduced (e.g., '25.1.0').
    This field is required to track API/config evolution."""

    deprecated_version: str | None = None
    """Version when this field was deprecated, if applicable.
    When set, indicates the field should no longer be used in new code."""

    deprecation_hint: str | None = None
    """Migration guidance for deprecated fields.
    Should explain what to use instead of this field."""


@dataclass(frozen=True)
class BackendAIConfigMeta(BackendAIFieldMeta):
    """Configuration field metadata.

    Extends BackendAIFieldMeta with configuration-specific fields like
    environment-specific examples and secret marking.
    """

    example: ConfigExample | None = None
    """Example value(s) for this configuration field.
    Use ConfigExample for environment-specific examples, or None if no example applies."""

    secret: bool = False
    """Whether this field contains sensitive information.
    When True, the value should be masked in logs, CLI output, and error messages."""

    composite: CompositeType | None = None
    """Type of composite field structure, or None for simple fields.

    - None: Simple field (not composite)
    - CompositeType.FIELD: Single nested object (e.g., DatabaseConfig)
    - CompositeType.DICT: Dictionary with string keys (e.g., dict[str, VolumeConfig])
    - CompositeType.LIST: List of objects (e.g., list[EndpointConfig])

    When set, example values are auto-generated from child field metadata
    rather than specified directly.
    """


@dataclass(frozen=True)
class BackendAIAPIMeta(BackendAIFieldMeta):
    """API field metadata for request/response DTOs and GraphQL types.

    Extends BackendAIFieldMeta with API-specific fields for documentation
    generation and schema introspection.
    """

    example: ConfigExample | None = None
    """Example value for API documentation.
    Use ConfigExample for environment-specific examples."""

    composite: bool = False
    """Whether this field is a composite type with nested fields.
    When True, example values are auto-generated from child field metadata
    rather than specified directly."""


def get_field_meta(
    model: type[BaseModel],
    field_name: str,
) -> BackendAIFieldMeta | None:
    """Retrieve BackendAI metadata for a field.

    Extracts the BackendAIFieldMeta (or subclass) from a Pydantic model field's
    Annotated type annotations. In Pydantic v2, metadata from Annotated types
    is stored in FieldInfo.metadata.

    Args:
        model: The Pydantic model class containing the field.
        field_name: The name of the field to retrieve metadata for.

    Returns:
        The BackendAIFieldMeta instance if found, None otherwise.

    Example:
        >>> class MyConfig(BaseModel):
        ...     name: Annotated[str, Field(), BackendAIConfigMeta(
        ...         description="Config name",
        ...         added_version="25.1.0",
        ...     )]
        >>> meta = get_field_meta(MyConfig, "name")
        >>> meta.description
        'Config name'
    """
    field_info = model.model_fields.get(field_name)
    if field_info is None:
        return None

    # In Pydantic v2, Annotated metadata is stored in FieldInfo.metadata
    for meta in field_info.metadata:
        if isinstance(meta, BackendAIFieldMeta):
            return meta
    return None


def get_field_type(model: type[BaseModel], field_name: str) -> type | None:
    """Get the actual type of a field.

    In Pydantic v2, Annotated types are already unwrapped by the time they're
    stored in FieldInfo.annotation, so this function simply returns the annotation.

    Args:
        model: The Pydantic model class containing the field.
        field_name: The name of the field.

    Returns:
        The underlying type of the field, or None if field doesn't exist.

    Example:
        >>> class MyConfig(BaseModel):
        ...     name: Annotated[str, Field()]
        >>> get_field_type(MyConfig, "name")
        <class 'str'>
    """
    field_info = model.model_fields.get(field_name)
    if field_info is None:
        return None

    # In Pydantic v2, annotation is already unwrapped from Annotated
    return field_info.annotation


def generate_example(
    model: type[BaseModel],
    field_name: str,
    env: ConfigEnvironment = ConfigEnvironment.LOCAL,
) -> str:
    """Generate example value for a field.

    Args:
        model: The Pydantic model class containing the field.
        field_name: The name of the field.
        env: The environment to get the example for.

    Returns:
        The example value as a string.

    Raises:
        ValueError: If field has no BackendAIConfigMeta/BackendAIAPIMeta or no example defined.

    Example:
        >>> generate_example(MyConfig, "server_addr", ConfigEnvironment.LOCAL)
        '127.0.0.1:8080'
        >>> generate_example(MyConfig, "server_addr", ConfigEnvironment.PROD)
        'api.example.com:8080'
    """
    meta = get_field_meta(model, field_name)

    if meta is None:
        raise ValueError(f"Field '{field_name}' in {model.__name__} has no BackendAI metadata")

    # Only BackendAIAPIMeta and BackendAIConfigMeta have example
    if not isinstance(meta, (BackendAIAPIMeta, BackendAIConfigMeta)):
        raise ValueError(
            f"Field '{field_name}' in {model.__name__} has unsupported metadata type: {type(meta).__name__}"
        )

    if meta.example is None:
        raise ValueError(f"Field '{field_name}' in {model.__name__} has no example defined")

    return meta.example.get(env)


def generate_composite_example(
    model: type[BaseModel],
    env: ConfigEnvironment = ConfigEnvironment.LOCAL,
) -> dict[str, Any]:
    """Recursively generate example for composite types from child fields.

    Traverses all fields in a model and builds a complete example dict
    by collecting example values from each field's metadata.

    Args:
        model: The Pydantic model class to generate examples for.
        env: The environment to get examples for.

    Returns:
        A dictionary mapping field names to their example values.

    Example:
        >>> class SessionConfig(BaseModel):
        ...     cpu: Annotated[int, BackendAIConfigMeta(
        ...         description="CPU cores", added_version="25.1.0",
        ...         example=ConfigExample(local="2", prod="8")
        ...     )]
        >>> generate_composite_example(SessionConfig, ConfigEnvironment.PROD)
        {'cpu': '8'}
    """
    result: dict[str, Any] = {}

    for name in model.model_fields:
        meta = get_field_meta(model, name)

        if meta is None:
            continue

        if not isinstance(meta, (BackendAIAPIMeta, BackendAIConfigMeta)):
            continue

        if meta.composite:
            # Recursively process child fields
            child_type = get_field_type(model, name)
            if (
                child_type is not None
                and isinstance(child_type, type)
                and issubclass(child_type, PydanticBaseModel)
            ):
                result[name] = generate_composite_example(child_type, env)
        else:
            # Use direct example
            if meta.example is not None:
                result[name] = meta.example.get(env)

    return result


def generate_model_example(
    model: type[BaseModel],
    env: ConfigEnvironment = ConfigEnvironment.LOCAL,
) -> dict[str, Any]:
    """Generate example for entire model by collecting all field examples.

    Skips composite fields (which have no direct example value).

    Args:
        model: The Pydantic model class to generate examples for.
        env: The environment to get examples for.

    Returns:
        A dictionary mapping field names to their example values.

    Example:
        >>> class CreateSessionRequest(BaseModel):
        ...     name: Annotated[str, BackendAIConfigMeta(
        ...         description="Session name", added_version="25.1.0",
        ...         example=ConfigExample(local="dev-session", prod="prod-session")
        ...     )]
        >>> generate_model_example(CreateSessionRequest, ConfigEnvironment.PROD)
        {'name': 'prod-session'}
    """
    result: dict[str, Any] = {}

    for name in model.model_fields:
        meta = get_field_meta(model, name)

        if meta is None:
            continue

        if not isinstance(meta, (BackendAIAPIMeta, BackendAIConfigMeta)):
            continue

        # Skip composite fields - they have no direct example
        if meta.composite:
            continue

        if meta.example is not None:
            result[name] = meta.example.get(env)

    return result
