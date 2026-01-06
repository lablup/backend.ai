from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel

__all__ = (
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

    example: ConfigExample | str | None = None
    """Example value(s) for this configuration field.
    Can be a ConfigExample for environment-specific examples,
    a simple string for universal examples, or None if no example applies."""

    secret: bool = False
    """Whether this field contains sensitive information.
    When True, the value should be masked in logs, CLI output, and error messages."""

    composite: bool = False
    """Whether this field is a composite type with nested fields.
    When True, example values are auto-generated from child field metadata
    rather than specified directly."""


@dataclass(frozen=True)
class BackendAIAPIMeta(BackendAIFieldMeta):
    """API field metadata for request/response DTOs and GraphQL types.

    Extends BackendAIFieldMeta with API-specific fields for documentation
    generation and schema introspection.
    """

    example: str | None = None
    """Example value for API documentation.
    Used in OpenAPI schemas and GraphQL documentation."""

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


def generate_example(model: type[BaseModel], field_name: str) -> str | dict[str, Any]:
    """Generate example value for a field.

    For fields with composite=False, returns the direct example value.
    For fields with composite=True, recursively generates examples from child fields.

    Args:
        model: The Pydantic model class containing the field.
        field_name: The name of the field.

    Returns:
        The example value as a string or dict. Returns empty string if no metadata found.

    Example:
        >>> # For a composite field, returns nested dict of child examples
        >>> generate_example(ParentConfig, "nested_config")
        {'child_field': 'example_value'}
    """
    meta = get_field_meta(model, field_name)

    if meta is None:
        return ""

    # Only BackendAIAPIMeta and BackendAIConfigMeta have composite and example
    if not isinstance(meta, (BackendAIAPIMeta, BackendAIConfigMeta)):
        return ""

    # If composite=False, use direct example
    if not meta.composite:
        if meta.example is None:
            return ""
        if isinstance(meta.example, ConfigExample):
            # For ConfigExample, return both local and prod
            return {"local": meta.example.local, "prod": meta.example.prod}
        return meta.example

    # If composite=True, generate from child fields
    field_type = get_field_type(model, field_name)
    if field_type is None:
        return ""

    # Check if field_type is a Pydantic model
    from pydantic import BaseModel as PydanticBaseModel

    if isinstance(field_type, type) and issubclass(field_type, PydanticBaseModel):
        return generate_composite_example(field_type)

    return ""


def generate_composite_example(model: type[BaseModel]) -> dict[str, Any]:
    """Recursively generate example for composite types from child fields.

    Traverses all fields in a model and builds a complete example dict
    by collecting example values from each field's metadata.

    Args:
        model: The Pydantic model class to generate examples for.

    Returns:
        A dictionary mapping field names to their example values.

    Example:
        >>> class SessionConfig(BaseModel):
        ...     cpu: Annotated[int, BackendAIAPIMeta(
        ...         description="CPU cores", added_version="25.1.0", example="4"
        ...     )]
        ...     memory: Annotated[str, BackendAIAPIMeta(
        ...         description="Memory size", added_version="25.1.0", example="8g"
        ...     )]
        >>> generate_composite_example(SessionConfig)
        {'cpu': '4', 'memory': '8g'}
    """
    from pydantic import BaseModel as PydanticBaseModel

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
                result[name] = generate_composite_example(child_type)
        else:
            # Use direct example
            if meta.example is not None:
                if isinstance(meta.example, ConfigExample):
                    result[name] = {"local": meta.example.local, "prod": meta.example.prod}
                else:
                    result[name] = meta.example

    return result


def generate_model_example(model: type[BaseModel]) -> dict[str, Any]:
    """Generate example for entire model by collecting all field examples.

    Args:
        model: The Pydantic model class to generate examples for.

    Returns:
        A dictionary mapping field names to their example values.

    Example:
        >>> class CreateSessionRequest(BaseModel):
        ...     name: Annotated[str, BackendAIAPIMeta(
        ...         description="Session name", added_version="25.1.0", example="my-session"
        ...     )]
        ...     config: Annotated[SessionConfig, BackendAIAPIMeta(
        ...         description="Session config", added_version="25.1.0", composite=True
        ...     )]
        >>> generate_model_example(CreateSessionRequest)
        {'name': 'my-session', 'config': {'cpu': '4', 'memory': '8g'}}
    """
    result: dict[str, Any] = {}

    for name in model.model_fields:
        example = generate_example(model, name)
        if example:
            result[name] = example

    return result
