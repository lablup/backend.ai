from __future__ import annotations

import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

from ai.backend.common.configs.inspector import ConfigInspector, FieldSchema
from ai.backend.common.meta import ConfigEnvironment

from .formatter import CompositeFormatter, create_default_formatter
from .types import FieldVisibility, GeneratorConfig

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = (
    "TOMLGenerator",
    "generate_sample_toml",
    "generate_halfstack_toml",
)


class TOMLGenerator:
    """Generates TOML configuration files from Pydantic models.

    Uses ConfigInspector to extract field metadata and BackendAIConfigMeta
    for documentation and examples. Supports environment-specific examples
    (LOCAL/PROD) and proper formatting of special types.

    Example:
        >>> from ai.backend.manager.config.unified import ManagerUnifiedConfig
        >>> generator = TOMLGenerator(env=ConfigEnvironment.LOCAL)
        >>> toml_content = generator.generate(ManagerUnifiedConfig)
        >>> generator.generate_to_file(ManagerUnifiedConfig, "halfstack.toml")
    """

    def __init__(
        self,
        env: ConfigEnvironment = ConfigEnvironment.LOCAL,
        formatter: CompositeFormatter | None = None,
        config: GeneratorConfig | None = None,
    ) -> None:
        """Initialize the TOML generator.

        Args:
            env: Target environment for examples (LOCAL or PROD).
            formatter: Value formatter for special types.
                If None, uses default formatter.
            config: Generator configuration options.
                If None, uses default configuration.
        """
        self._inspector = ConfigInspector(env=env)
        self._formatter = formatter or create_default_formatter()
        self._config = config or GeneratorConfig()

    @property
    def env(self) -> ConfigEnvironment:
        """The target environment for example values."""
        return self._inspector.env

    def generate(self, model: type[BaseModel]) -> str:
        """Generate TOML configuration string from a Pydantic model.

        Args:
            model: The Pydantic model class to generate configuration for.

        Returns:
            A string containing the TOML configuration with comments.
        """
        schema = self._inspector.extract(model)
        lines = self._generate_schema(schema, path=[])
        return "\n".join(lines)

    def generate_to_file(
        self,
        model: type[BaseModel],
        output_path: str | Path,
        header: str | None = None,
    ) -> None:
        """Generate TOML configuration and write to file.

        Args:
            model: The Pydantic model class to generate configuration for.
            output_path: Path where the configuration file will be written.
            header: Optional header comment to add at the top of the file.
        """
        content = self.generate(model)
        output = Path(output_path)

        with output.open("w", encoding="utf-8") as f:
            if header:
                f.write(self._wrap_comment(header, ""))
                f.write("\n\n")
            f.write(content)
            f.write("\n")

    def _generate_schema(
        self,
        schema: Mapping[str, FieldSchema],
        path: list[str],
    ) -> list[str]:
        """Generate TOML lines from schema.

        Args:
            schema: Mapping of field keys to schemas.
            path: Current path in the configuration hierarchy.

        Returns:
            List of TOML lines.
        """
        lines: list[str] = []

        # Categorize fields
        simple, composite, arrays = self._categorize_fields(schema)

        # 1. Simple fields first
        for key, field in simple.items():
            field_lines = self._generate_field(key, field, path)
            lines.extend(field_lines)

        # 2. Composite sections [section.name]
        for key, field in composite.items():
            section_lines = self._generate_section(key, field, path)
            lines.extend(section_lines)

        # 3. Array of tables [[array.name]]
        for key, field in arrays.items():
            array_lines = self._generate_array_section(key, field, path)
            lines.extend(array_lines)

        return lines

    def _generate_field(
        self,
        key: str,
        field: FieldSchema,
        path: list[str],
    ) -> list[str]:
        """Generate TOML lines for a single field.

        Args:
            key: The field key.
            field: The field schema.
            path: Current path in hierarchy.

        Returns:
            List of TOML lines for this field.
        """
        lines: list[str] = []
        indent = self._get_indent(len(path))

        # Check visibility
        visibility = self._get_visibility(field)
        if visibility == FieldVisibility.HIDDEN:
            return []

        # Skip deprecated if configured
        if not self._config.show_deprecated and field.doc.deprecated_version:
            return []

        # Add description comment
        if field.doc.description:
            comment_lines = self._wrap_comment(field.doc.description, indent)
            lines.append(comment_lines)

        # Add version comment if configured
        if self._config.include_version_comments:
            lines.append(f"{indent}# Added in {field.doc.added_version}")
            if field.doc.deprecated_version:
                hint = field.doc.deprecation_hint or ""
                lines.append(f"{indent}# DEPRECATED in {field.doc.deprecated_version}: {hint}")

        # Get example value
        example_value = self._get_field_value(field)

        # Format the value
        formatted = self._formatter.format(example_value, field)

        # Build the line
        value_str = formatted.value
        if formatted.comment:
            value_str = f"{value_str}  {formatted.comment}"

        match visibility:
            case FieldVisibility.REQUIRED:
                lines.append(f"{indent}{key} = {value_str}")
            case FieldVisibility.OPTIONAL:
                lines.append(f"{indent}## {key} = {value_str}")

        return lines

    def _generate_section(
        self,
        key: str,
        field: FieldSchema,
        path: list[str],
    ) -> list[str]:
        """Generate TOML section [section.name].

        Args:
            key: The section key.
            field: The field schema.
            path: Current path in hierarchy.

        Returns:
            List of TOML lines for this section.
        """
        lines: list[str] = []
        indent = self._get_indent(len(path))
        section_path = path + [key]

        # Check visibility
        visibility = self._get_visibility(field)
        if visibility == FieldVisibility.HIDDEN:
            return []

        # Add blank line before section
        lines.append("")

        # Add description comment
        if field.doc.description:
            comment_lines = self._wrap_comment(field.doc.description, indent)
            lines.append(comment_lines)

        # Section header
        section_name = ".".join(section_path)
        if visibility == FieldVisibility.OPTIONAL:
            lines.append(f"{indent}## [{section_name}]")
        else:
            lines.append(f"{indent}[{section_name}]")

        # Child fields
        if field.children:
            child_lines = self._generate_schema(field.children, section_path)
            lines.extend(child_lines)

        return lines

    def _generate_array_section(
        self,
        key: str,
        field: FieldSchema,
        path: list[str],
    ) -> list[str]:
        """Generate TOML array of tables [[array.name]].

        Args:
            key: The array key.
            field: The field schema.
            path: Current path in hierarchy.

        Returns:
            List of TOML lines for this array section.
        """
        lines: list[str] = []
        indent = self._get_indent(len(path))
        section_path = path + [key]

        # Check visibility
        visibility = self._get_visibility(field)
        if visibility == FieldVisibility.HIDDEN:
            return []

        # Add blank line before section
        lines.append("")

        # Add description comment
        if field.doc.description:
            comment_lines = self._wrap_comment(field.doc.description, indent)
            lines.append(comment_lines)

        # Array of tables header
        section_name = ".".join(section_path)
        lines.append(f"{indent}[[{section_name}]]")
        lines.append(f"{indent}# Add multiple [[{section_name}]] sections as needed")

        # Child fields
        if field.children:
            child_lines = self._generate_schema(field.children, section_path)
            lines.extend(child_lines)

        return lines

    def _get_visibility(self, field: FieldSchema) -> FieldVisibility:
        """Determine field visibility in output.

        Args:
            field: The field schema.

        Returns:
            FieldVisibility indicating how to display the field.
        """
        # Hide runtime-injected fields
        if "at runtime" in field.doc.description.lower():
            return FieldVisibility.HIDDEN

        # Optional fields are commented out
        if not field.type_info.required:
            return FieldVisibility.OPTIONAL

        return FieldVisibility.REQUIRED

    def _get_field_value(self, field: FieldSchema) -> str:
        """Get the value to use for a field.

        Priority: example value > default > placeholder

        Args:
            field: The field schema.

        Returns:
            The value string to use in output.
        """
        # Handle secrets
        if field.type_info.secret and self._config.mask_secrets:
            return self._config.secret_placeholder

        # Try example value first
        example = self._inspector.get_example_value(field)
        if example is not None:
            return example

        # Fall back to default
        if field.type_info.default is not None:
            return field.type_info.default

        # Placeholder based on type
        return self._get_type_placeholder(field.type_info.type_name)

    def _get_type_placeholder(self, type_name: str) -> str:
        """Get a placeholder value for a type.

        Args:
            type_name: The type name.

        Returns:
            A placeholder string for the type.
        """
        type_lower = type_name.lower()

        if "str" in type_lower:
            return "..."
        if "int" in type_lower:
            return "0"
        if "float" in type_lower:
            return "0.0"
        if "bool" in type_lower:
            return "false"
        if "list" in type_lower or "sequence" in type_lower:
            return "[]"
        if "dict" in type_lower or "mapping" in type_lower:
            return "{}"
        if "path" in type_lower:
            return "/path/to/file"
        if "binarysize" in type_lower:
            return "1G"
        if "hostportpair" in type_lower:
            return '{ host = "localhost", port = 0 }'

        return "..."

    def _get_indent(self, level: int) -> str:
        """Get indentation string for a nesting level.

        Args:
            level: The nesting level.

        Returns:
            Indentation string.
        """
        return " " * (self._config.indent_size * level)

    def _wrap_comment(self, text: str, indent: str) -> str:
        """Wrap text as TOML comments.

        Args:
            text: The text to wrap.
            indent: Indentation prefix.

        Returns:
            Wrapped comment string.
        """
        # Calculate available width
        available_width = self._config.comment_width - len(indent) - 2  # 2 for "# "

        lines = text.strip().split("\n")
        result_lines: list[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                result_lines.append(f"{indent}#")
            else:
                wrapped = textwrap.wrap(line, width=available_width)
                for wrapped_line in wrapped:
                    result_lines.append(f"{indent}# {wrapped_line}")

        return "\n".join(result_lines)

    def _categorize_fields(
        self,
        schema: Mapping[str, FieldSchema],
    ) -> tuple[
        dict[str, FieldSchema],  # simple fields
        dict[str, FieldSchema],  # composite (object) fields
        dict[str, FieldSchema],  # array fields
    ]:
        """Categorize fields by type.

        Args:
            schema: The schema to categorize.

        Returns:
            Tuple of (simple, composite, arrays) field dictionaries.
        """
        simple: dict[str, FieldSchema] = {}
        composite: dict[str, FieldSchema] = {}
        arrays: dict[str, FieldSchema] = {}

        for key, field in schema.items():
            type_name = field.type_info.type_name.lower()

            # Check if it's a composite field with children
            if field.children is not None:
                # Check if it's an array type
                if "list" in type_name or "sequence" in type_name:
                    arrays[key] = field
                else:
                    composite[key] = field
            else:
                simple[key] = field

        return simple, composite, arrays


def generate_sample_toml(
    model: type[BaseModel],
    output_path: str | Path | None = None,
    header: str | None = None,
) -> str:
    """Generate sample.toml with PROD environment examples.

    Convenience function for generating production configuration samples.

    Args:
        model: The Pydantic model class.
        output_path: Optional path to write the file.
        header: Optional header comment.

    Returns:
        The generated TOML content.
    """
    generator = TOMLGenerator(env=ConfigEnvironment.PROD)
    content = generator.generate(model)

    if output_path:
        generator.generate_to_file(model, output_path, header)

    return content


def generate_halfstack_toml(
    model: type[BaseModel],
    output_path: str | Path | None = None,
    header: str | None = None,
) -> str:
    """Generate halfstack.toml with LOCAL environment examples.

    Convenience function for generating local development configuration.

    Args:
        model: The Pydantic model class.
        output_path: Optional path to write the file.
        header: Optional header comment.

    Returns:
        The generated TOML content.
    """
    generator = TOMLGenerator(env=ConfigEnvironment.LOCAL)
    content = generator.generate(model)

    if output_path:
        generator.generate_to_file(model, output_path, header)

    return content
