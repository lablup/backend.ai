from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from ai.backend.common.meta import (
    BackendAIConfigMeta,
    BackendAIFieldMeta,
    CompositeType,
    ConfigEnvironment,
    ConfigExample,
    get_field_meta,
)

from .types import FieldDocumentation, FieldSchema, FieldTypeInfo

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ("ConfigInspector",)


class ConfigInspector:
    """Inspects and extracts structured information from BaseConfigSchema subclasses.

    This inspector uses BackendAIConfigMeta annotations to build a complete
    schema representation including type information, documentation,
    and nested structures for composite fields.

    Example:
        >>> from ai.backend.manager.config.unified import ManagerUnifiedConfig
        >>> inspector = ConfigInspector()
        >>> schema = inspector.extract(ManagerUnifiedConfig)
        >>> for key, field_schema in schema.items():
        ...     print(f"{key}: {field_schema.doc.description}")
    """

    def __init__(self, env: ConfigEnvironment = ConfigEnvironment.LOCAL) -> None:
        """Initialize the inspector with target environment.

        Args:
            env: The configuration environment for extracting examples.
                Defaults to LOCAL for development-friendly defaults.
        """
        self._env = env

    @property
    def env(self) -> ConfigEnvironment:
        """The current environment for example extraction."""
        return self._env

    def extract(self, model: type[BaseModel]) -> Mapping[str, FieldSchema]:
        """Extract complete schema from a Pydantic model.

        Args:
            model: The Pydantic model class (typically a BaseConfigSchema subclass).

        Returns:
            A mapping of field keys to their complete schema information.
        """
        result: dict[str, FieldSchema] = {}

        for field_name, field_info in model.model_fields.items():
            field_schema = self._extract_field(model, field_name, field_info)
            if field_schema is not None:
                result[field_schema.key] = field_schema

        return result

    def _extract_field(
        self,
        model: type[BaseModel],
        field_name: str,
        field_info: FieldInfo,
    ) -> FieldSchema | None:
        """Extract schema for a single field.

        Args:
            model: The parent model class.
            field_name: The Python field name.
            field_info: Pydantic field information.

        Returns:
            The extracted FieldSchema, or None if the field lacks metadata.
        """
        # Get BackendAI metadata
        meta = get_field_meta(model, field_name)
        if meta is None:
            # Skip fields without BackendAI metadata
            return None

        # Determine the TOML key
        key = self._get_field_key(field_name, field_info)

        # Extract type information
        type_info = self._extract_type_info(field_info, meta)

        # Extract documentation
        doc = self._extract_documentation(meta)

        # Extract children for composite fields
        children = self._extract_children(field_info, meta)

        return FieldSchema(
            key=key,
            type_info=type_info,
            doc=doc,
            children=children,
        )

    def _get_field_key(self, field_name: str, field_info: FieldInfo) -> str:
        """Determine the TOML key for a field.

        Uses serialization_alias if available, otherwise falls back to field_name.

        Args:
            field_name: The Python field name.
            field_info: Pydantic field information.

        Returns:
            The key to use in TOML output.
        """
        if field_info.serialization_alias is not None:
            return field_info.serialization_alias
        return field_name

    def _extract_type_info(
        self,
        field_info: FieldInfo,
        meta: BackendAIFieldMeta,
    ) -> FieldTypeInfo:
        """Extract type information from field.

        Args:
            field_info: Pydantic field information.
            meta: BackendAI metadata for the field.

        Returns:
            Extracted type information.
        """
        annotation = field_info.annotation

        # Get type name
        type_name = self._get_type_name(annotation)

        # Check if nullable (Type | None pattern) - this determines "optional" in TOML output
        # A field is required if it's NOT nullable, regardless of having a default value
        is_nullable = self._is_nullable_type(annotation)
        required = not is_nullable

        # Get default value
        default: Any = None
        if field_info.default is not PydanticUndefined:
            default = field_info.default
        elif field_info.default_factory is not None:
            # For default_factory, we might want to instantiate to get the value
            # But we store None to avoid side effects during extraction
            default = None

        # Check if secret and composite type (only for BackendAIConfigMeta)
        secret = False
        composite_type: CompositeType | None = None
        if isinstance(meta, BackendAIConfigMeta):
            secret = meta.secret
            composite_type = meta.composite

        return FieldTypeInfo(
            type_name=type_name,
            default=default,
            required=required,
            secret=secret,
            composite_type=composite_type,
        )

    def _get_type_name(self, annotation: type | None) -> str:
        """Get a human-readable type name from annotation.

        Args:
            annotation: The type annotation.

        Returns:
            A human-readable type name string.
        """
        if annotation is None:
            return "unknown"

        # Handle generic types (list[str], Optional[int], etc.)
        origin = getattr(annotation, "__origin__", None)
        if origin is not None:
            args = getattr(annotation, "__args__", ())
            origin_name = getattr(origin, "__name__", str(origin))

            # Special case for Union types (Optional)
            if origin_name == "Union":
                # Filter out NoneType for Optional representation
                non_none_args = [a for a in args if a is not type(None)]
                if len(non_none_args) == 1 and len(args) == 2:
                    inner_type = self._get_type_name(non_none_args[0])
                    return f"{inner_type} | None"
                arg_names = ", ".join(self._get_type_name(a) for a in args)
                return f"Union[{arg_names}]"

            if args:
                arg_names = ", ".join(self._get_type_name(a) for a in args)
                return f"{origin_name}[{arg_names}]"
            return origin_name

        # Handle regular classes
        if hasattr(annotation, "__name__"):
            return annotation.__name__

        return str(annotation)

    def _is_nullable_type(self, annotation: type | None) -> bool:
        """Check if a type annotation is nullable (Type | None).

        Args:
            annotation: The type annotation to check.

        Returns:
            True if the type is nullable (allows None), False otherwise.
        """
        import types

        if annotation is None:
            return True

        # Handle Python 3.10+ union syntax (str | None)
        if isinstance(annotation, types.UnionType):
            return type(None) in annotation.__args__

        origin = getattr(annotation, "__origin__", None)
        if origin is None:
            return False

        # Check for Union types (including Optional[T] which is Union[T, None])
        origin_name = getattr(origin, "__name__", str(origin))
        if origin_name == "Union":
            args = getattr(annotation, "__args__", ())
            # Check if NoneType is one of the union members
            return type(None) in args

        return False

    def _extract_documentation(
        self,
        meta: BackendAIFieldMeta,
    ) -> FieldDocumentation:
        """Extract documentation from metadata.

        Args:
            meta: BackendAI metadata for the field.

        Returns:
            Extracted documentation information.
        """
        example: ConfigExample | None = None
        if isinstance(meta, BackendAIConfigMeta) and meta.example is not None:
            example = meta.example

        return FieldDocumentation(
            description=meta.description,
            example=example,
            added_version=meta.added_version,
            deprecated_version=meta.deprecated_version,
            deprecation_hint=meta.deprecation_hint,
        )

    def _extract_children(
        self,
        field_info: FieldInfo,
        meta: BackendAIFieldMeta,
    ) -> Mapping[str, FieldSchema] | None:
        """Extract child schemas for composite fields.

        Args:
            field_info: Pydantic field information.
            meta: BackendAI metadata for the field.

        Returns:
            Child field schemas if composite, None otherwise.
        """
        # Check if this is a composite field
        if not isinstance(meta, BackendAIConfigMeta) or not meta.composite:
            return None

        annotation = field_info.annotation
        if annotation is None:
            return None

        # Unwrap Optional types
        annotation = self._unwrap_optional(annotation)

        # Extract the target type based on composite type
        target_type = self._get_composite_target_type(annotation, meta.composite)
        if target_type is None:
            return None

        # Extract children from the target BaseModel
        if isinstance(target_type, type) and issubclass(target_type, BaseModel):
            return self.extract(target_type)

        return None

    def _unwrap_optional(self, annotation: type) -> type:
        """Unwrap Optional[T] to get T."""
        import types

        # Handle Python 3.10+ UnionType (X | None syntax)
        if isinstance(annotation, types.UnionType):
            args = annotation.__args__
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                return non_none[0]
            return annotation

        # Handle typing.Union (Optional[X] syntax)
        origin = getattr(annotation, "__origin__", None)
        if origin is not None:
            args = getattr(annotation, "__args__", ())
            # Check for Optional (Union with None)
            if len(args) == 2 and type(None) in args:
                return [a for a in args if a is not type(None)][0]
        return annotation

    def _get_composite_target_type(
        self,
        annotation: type,
        composite: CompositeType | None,
    ) -> type | None:
        """Get the target type for children extraction based on composite type.

        Args:
            annotation: The field annotation (already unwrapped from Optional).
            composite: The composite type indicator.

        Returns:
            The target type to extract children from, or None if not found.
        """
        # FIELD: direct BaseModel
        if composite == CompositeType.FIELD:
            return annotation

        origin = getattr(annotation, "__origin__", None)
        args: tuple[type, ...] = getattr(annotation, "__args__", ())

        # DICT: dict[str, T] -> extract T
        if composite == CompositeType.DICT:
            if origin is not None:
                origin_name = getattr(origin, "__name__", str(origin))
                if origin_name in ("dict", "Mapping") and len(args) >= 2:
                    return args[1]  # Value type
            return None

        # LIST: list[T] -> extract T
        if composite == CompositeType.LIST:
            if origin is not None:
                origin_name = getattr(origin, "__name__", str(origin))
                if origin_name in ("list", "Sequence") and len(args) >= 1:
                    return args[0]  # Item type
            return None

        return None

    def get_example_value(self, field_schema: FieldSchema) -> str | None:
        """Get the example value for a field based on current environment.

        Args:
            field_schema: The field schema to get example for.

        Returns:
            The example string for current environment, or None if no example.
        """
        if field_schema.doc.example is None:
            return None
        return field_schema.doc.example.get(self._env)

    def get_fields_by_version(
        self,
        schema: Mapping[str, FieldSchema],
        *,
        descending: bool = True,
    ) -> list[tuple[str, FieldSchema]]:
        """Get fields sorted by added_version.

        Useful for showing recently added fields first in help output.

        Args:
            schema: The extracted schema mapping.
            descending: If True, newest versions first. Default True.

        Returns:
            List of (key, schema) tuples sorted by version.
        """
        items = list(schema.items())
        items.sort(
            key=lambda x: tuple(
                int(p) if p.isdigit() else p for p in x[1].doc.added_version.split(".")
            ),
            reverse=descending,
        )
        return items

    def get_deprecated_fields(
        self,
        schema: Mapping[str, FieldSchema],
    ) -> list[tuple[str, FieldSchema]]:
        """Get all deprecated fields.

        Args:
            schema: The extracted schema mapping.

        Returns:
            List of (key, schema) tuples for deprecated fields.
        """
        return [
            (key, field_schema)
            for key, field_schema in schema.items()
            if field_schema.doc.deprecated_version is not None
        ]

    def get_secret_fields(
        self,
        schema: Mapping[str, FieldSchema],
    ) -> list[tuple[str, FieldSchema]]:
        """Get all secret fields.

        Args:
            schema: The extracted schema mapping.

        Returns:
            List of (key, schema) tuples for secret fields.
        """
        return [
            (key, field_schema)
            for key, field_schema in schema.items()
            if field_schema.type_info.secret
        ]
