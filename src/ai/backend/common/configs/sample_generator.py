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


def _get_field_comment(field_schema: dict[str, Any]) -> str:
    """Generate comment for a field based on its schema."""
    comment_parts = []

    # Add description
    if "description" in field_schema:
        comment_parts.append(field_schema["description"].strip())

    # Add examples
    if "examples" in field_schema:
        examples_str = ", ".join(str(ex) for ex in field_schema["examples"])
        comment_parts.append(f"Examples: {examples_str}")

    return "\n".join(comment_parts)


def _get_default_from_schema(field_schema: dict[str, Any]) -> Any:
    """Get default value from JSON schema."""
    if "default" in field_schema:
        return field_schema["default"]

    # Handle different types with appropriate defaults
    field_type = field_schema.get("type")
    if field_type == "string":
        return ""
    elif field_type == "integer":
        return 0
    elif field_type == "number":
        return 0.0
    elif field_type == "boolean":
        return False
    elif field_type == "array":
        return []
    elif field_type == "object":
        return {}

    return None


def _generate_config_from_schema(
    schema: dict[str, Any], definitions: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Generate configuration dictionary from JSON schema."""
    if definitions is None:
        definitions = schema.get("$defs", {})

    config: dict[str, Any] = {}
    properties = schema.get("properties", {})

    for field_name, field_schema in properties.items():
        # Handle references to other schemas
        if "$ref" in field_schema:
            ref_name = field_schema["$ref"].split("/")[-1]
            if ref_name in definitions:
                ref_schema = definitions[ref_name]
                # Only recurse if it's an object type (likely a BaseModel)
                if ref_schema.get("type") == "object":
                    config[field_name] = _generate_config_from_schema(ref_schema, definitions)
                else:
                    config[field_name] = _get_default_from_schema(ref_schema)
            else:
                config[field_name] = None

        # Handle allOf (used for inheritance)
        elif "allOf" in field_schema:
            merged_schema = {}
            for sub_schema in field_schema["allOf"]:
                if "$ref" in sub_schema:
                    ref_name = sub_schema["$ref"].split("/")[-1]
                    if ref_name in definitions:
                        ref_schema = definitions[ref_name]
                        merged_schema.update(ref_schema)
                else:
                    merged_schema.update(sub_schema)

            if merged_schema.get("type") == "object":
                config[field_name] = _generate_config_from_schema(merged_schema, definitions)
            else:
                config[field_name] = _get_default_from_schema(merged_schema)

        # Handle anyOf/oneOf (used for Union types)
        elif "anyOf" in field_schema or "oneOf" in field_schema:
            variants = field_schema.get("anyOf", field_schema.get("oneOf", []))

            # Find the first non-null variant
            for variant in variants:
                if variant.get("type") != "null":
                    if "$ref" in variant:
                        ref_name = variant["$ref"].split("/")[-1]
                        if ref_name in definitions:
                            ref_schema = definitions[ref_name]
                            if ref_schema.get("type") == "object":
                                config[field_name] = _generate_config_from_schema(
                                    ref_schema, definitions
                                )
                            else:
                                config[field_name] = _get_default_from_schema(ref_schema)
                        else:
                            config[field_name] = None
                    else:
                        if variant.get("type") == "object":
                            config[field_name] = _generate_config_from_schema(variant, definitions)
                        else:
                            config[field_name] = _get_default_from_schema(variant)
                    break
            else:
                # All variants are null or no suitable variant found
                config[field_name] = None

        # Handle object type (nested models)
        elif field_schema.get("type") == "object":
            config[field_name] = _generate_config_from_schema(field_schema, definitions)

        # Handle primitive types
        else:
            config[field_name] = _get_default_from_schema(field_schema)

    return config


def _add_field_comments_from_schema(
    toml_str: str, schema: dict[str, Any], definitions: Optional[dict[str, Any]] = None
) -> str:
    """Add comments to TOML string based on JSON schema."""
    if definitions is None:
        definitions = schema.get("$defs", {})

    lines = toml_str.split("\n")
    commented_lines = []
    current_section = None
    current_schema = schema

    for line in lines:
        line = line.rstrip()

        # Detect section headers
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            commented_lines.append("")
            commented_lines.append(line)

            # Navigate to the schema for this section
            current_schema = schema
            section_parts = current_section.split(".")
            for part in section_parts:
                properties = current_schema.get("properties", {})
                if part in properties:
                    field_schema = properties[part]
                    # Resolve references
                    if "$ref" in field_schema:
                        ref_name = field_schema["$ref"].split("/")[-1]
                        if ref_name in definitions:
                            current_schema = definitions[ref_name]
                    elif field_schema.get("type") == "object":
                        current_schema = field_schema
            continue

        # Skip empty lines
        if not line.strip():
            commented_lines.append(line)
            continue

        # Extract field name from key = value line
        if "=" in line:
            key = line.split("=")[0].strip()
            field_name = key.strip('"')

            # Find the field schema
            properties = current_schema.get("properties", {})
            if field_name in properties:
                field_schema = properties[field_name]

                # Resolve references for comment extraction
                if "$ref" in field_schema:
                    ref_name = field_schema["$ref"].split("/")[-1]
                    if ref_name in definitions:
                        field_schema = definitions[ref_name]

                # Add comment if description exists
                comment = _get_field_comment(field_schema)
                if comment:
                    commented_lines.append(_wrap_comment(comment))

        commented_lines.append(line)

    return "\n".join(commented_lines)


def generate_sample_config(model_class: Type[BaseModel]) -> str:
    """
    Generate a sample TOML configuration file from a Pydantic model.

    Args:
        model_class: The Pydantic model class to generate configuration for

    Returns:
        A string containing the TOML configuration with comments
    """
    # Get JSON schema from the model
    schema = model_class.model_json_schema()

    # Generate configuration dictionary from schema
    config_dict = _generate_config_from_schema(schema)

    # Generate basic TOML
    toml_str = toml.dumps(config_dict)

    # Add comments based on schema
    commented_toml = _add_field_comments_from_schema(toml_str, schema)

    return commented_toml


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
    config_content = generate_sample_config(model_class)

    with open(output_path, "w") as f:
        if header_comment:
            f.write(_wrap_comment(header_comment))
            f.write("\n\n")
        f.write(config_content)
