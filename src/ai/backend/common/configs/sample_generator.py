"""
Sample configuration generator for Backend.AI.

This module provides utilities to generate sample TOML configuration files
from Pydantic models by extracting field information, defaults, descriptions,
and examples using JSON Schema.
"""

import textwrap
from typing import Any, Optional, Type

import toml
from pydantic import BaseModel


def _wrap_comment(text: str, width: int = 80) -> str:
    """Wrap text into multiline comment format."""
    lines = text.strip().split("\n")
    wrapped_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            wrapped_lines.append("#")
        else:
            # Wrap long lines
            wrapped = textwrap.wrap(line, width=width - 2)  # Account for '# '
            for wrapped_line in wrapped:
                wrapped_lines.append(f"# {wrapped_line}")

    return "\n".join(wrapped_lines)


def _generate_sample_config(model_class: Type[BaseModel]) -> str:
    """
    Generate a sample TOML configuration file from a Pydantic model.

    Args:
        model_class: The Pydantic model class to generate configuration for

    Returns:
        A string containing the TOML configuration with comments
    """
    schema = model_class.model_json_schema()

    def _get_field_info(model_cls: Type[BaseModel], field_name: str) -> dict[str, Any]:
        """Extract field information from Pydantic model including Field metadata."""
        field_info = {}
        if hasattr(model_cls, "model_fields"):
            # Try to find field by name or alias
            field = None
            if field_name in model_cls.model_fields:
                field = model_cls.model_fields[field_name]
            else:
                # Search by alias (serialization_alias or validation_alias)
                for finfo in model_cls.model_fields.values():
                    if (
                        hasattr(finfo, "serialization_alias")
                        and finfo.serialization_alias == field_name
                    ):
                        field = finfo
                        break
                    if hasattr(finfo, "validation_alias"):
                        alias_choices = finfo.validation_alias
                        if hasattr(alias_choices, "choices") and field_name in getattr(
                            alias_choices, "choices", []
                        ):
                            field = finfo
                            break

            if field:
                field_info["description"] = field.description

                # Handle default values properly, including enums and default_factory
                if field.default is not ...:
                    default_val = field.default
                    # If it's an enum, get its value
                    if hasattr(default_val, "value"):
                        field_info["default"] = default_val.value
                    else:
                        field_info["default"] = default_val
                elif hasattr(field, "default_factory") and field.default_factory is not None:
                    # Handle default_factory case - create instance to get defaults
                    try:
                        factory_instance = field.default_factory()  # type: ignore
                        if hasattr(factory_instance, "model_dump"):
                            # It's a Pydantic model, get its default values
                            field_info["factory_defaults"] = factory_instance.model_dump()
                    except Exception:
                        # If factory fails, just set to None
                        pass
                    field_info["default"] = None
                else:
                    field_info["default"] = None

                field_info["examples"] = getattr(field, "examples", None)
        return field_info

    def _process_property(
        prop_name: str,
        prop_schema: dict[str, Any],
        required: bool = False,
        indent: int = 0,
        model_cls: Optional[Type[BaseModel]] = None,
    ) -> list[str]:
        """Process a single property and return TOML lines with comments."""
        lines = []
        indent_str = "  " * indent

        # Get field information from Pydantic model if available
        field_info = {}
        if model_cls:
            field_info = _get_field_info(model_cls, prop_name)

        # Add description as comment if available
        description = field_info.get("description") or prop_schema.get("description")
        if description:
            comment_lines = _wrap_comment(description)
            for line in comment_lines.split("\n"):
                lines.append(f"{indent_str}{line}")

        # Get the value to use - prioritize Field examples over schema examples
        value = None

        # Try Field examples first
        if field_info.get("examples"):
            value = field_info["examples"][0]
        elif (
            field_info.get("default") is not None
            and str(field_info["default"]) != "PydanticUndefined"
        ):
            value = field_info["default"]
        # Fall back to schema examples
        elif "example" in prop_schema:
            value = prop_schema["example"]
        elif "examples" in prop_schema and prop_schema["examples"]:
            value = prop_schema["examples"][0]
        elif "default" in prop_schema:
            value = prop_schema["default"]
        else:
            # Generate default based on type
            prop_type = prop_schema.get("type", "string")
            if prop_type == "string":
                value = ""
            elif prop_type == "integer":
                value = 0
            elif prop_type == "number":
                value = 0.0
            elif prop_type == "boolean":
                value = False
            elif prop_type == "array":
                value = []
            elif prop_type == "object":
                value = {}
            else:
                value = None

        # Format the property line
        if value is not None:
            if isinstance(value, dict):
                # Skip inline dict representation, will be handled as section
                return lines
            else:
                # Use example values when available, comment out only if no example and not required
                should_comment = not required and (
                    not field_info.get("examples")
                    and "example" not in prop_schema
                    and "examples" not in prop_schema
                )
                prefix = "# " if should_comment else ""
                lines.append(
                    f"{indent_str}{prefix}{prop_name} = {toml.dumps({prop_name: value}).strip().split(' = ', 1)[1]}"
                )

        return lines

    def _process_schema(
        schema_dict: dict[str, Any],
        path: Optional[list[str]] = None,
        parent_required: Optional[list[str]] = None,
        model_cls: Optional[Type[BaseModel]] = None,
    ) -> list[str]:
        """Recursively process schema and generate TOML lines."""
        if path is None:
            path = []
        if parent_required is None:
            parent_required = []

        lines = []
        properties = schema_dict.get("properties", {})
        required = schema_dict.get("required", [])

        # Group properties by type
        simple_props = {}
        object_props = {}

        for prop_name, prop_schema in properties.items():
            if "$ref" in prop_schema:
                # Resolve reference
                ref_path = prop_schema["$ref"].split("/")
                if ref_path[0] == "#" and len(ref_path) > 1:
                    resolved = schema
                    for part in ref_path[1:]:
                        resolved = resolved.get(part, {})
                    prop_schema = resolved

            prop_type = prop_schema.get("type", "")

            if prop_type == "object" or "properties" in prop_schema:
                object_props[prop_name] = prop_schema
            else:
                simple_props[prop_name] = prop_schema

        # Add simple properties first
        for prop_name, prop_schema in simple_props.items():
            is_required = prop_name in required or prop_name in parent_required
            prop_lines = _process_property(
                prop_name, prop_schema, required=is_required, indent=len(path), model_cls=model_cls
            )
            if prop_lines:
                lines.extend(prop_lines)

        # Add object properties as sections
        for prop_name, prop_schema in object_props.items():
            if lines and lines[-1].strip():  # Add blank line before section
                lines.append("")

            # Add section comment
            if "description" in prop_schema:
                comment_lines = _wrap_comment(prop_schema["description"])
                lines.extend(comment_lines.split("\n"))

            # Add section header
            section_path = path + [prop_name]
            section_header = "[" + ".".join(section_path) + "]"
            lines.append(section_header)

            # Process nested properties - try to get nested model class
            nested_model_cls = None
            if model_cls and hasattr(model_cls, "model_fields"):
                field_info = _get_field_info(model_cls, prop_name)
                if field_info:
                    # First try to find the field by name or alias
                    field = None
                    if prop_name in model_cls.model_fields:
                        field = model_cls.model_fields[prop_name]
                    else:
                        # Search by alias
                        for finfo in model_cls.model_fields.values():
                            if (
                                hasattr(finfo, "serialization_alias")
                                and finfo.serialization_alias == prop_name
                            ):
                                field = finfo
                                break

                    if field:
                        if hasattr(field, "annotation") and hasattr(field.annotation, "__origin__"):
                            # Handle generic types
                            args = getattr(field.annotation, "__args__", ())
                            if args and hasattr(args[0], "model_fields"):
                                nested_model_cls = args[0]
                        elif hasattr(field.annotation, "model_fields"):
                            nested_model_cls = field.annotation

            nested_lines = _process_schema(
                prop_schema, path=section_path, parent_required=required, model_cls=nested_model_cls
            )
            lines.extend(nested_lines)

        return lines

    # Process the root schema
    lines = _process_schema(schema, model_cls=model_class)

    return "\n".join(lines)


def generate_sample_config_file(
    model_class: Type[BaseModel], output_path: str, header_comment: Optional[str] = None
) -> None:
    """
    Generate a sample TOML configuration file and write it to disk.

    Args:
        model_class: The Pydantic model class to generate configuration for
        output_path: Path where the configuration file will be written
        header_comment: Optional header comment to add at the top of the file
    """
    config_content = _generate_sample_config(model_class)

    with open(output_path, "w") as f:
        if header_comment:
            f.write(_wrap_comment(header_comment))
            f.write("\n\n")
        f.write(config_content)
        f.write("\n")
