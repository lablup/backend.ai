"""
Sample configuration generator for Backend.AI.

This module provides utilities to generate sample TOML configuration files
from Pydantic models by extracting field information, defaults, descriptions,
and examples using JSON Schema.
"""

import enum
import logging
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from pathlib import PosixPath, PurePath
from typing import Any, Optional, Type

import toml
from pydantic import BaseModel
from pydantic_core import PydanticUndefined
from toml.decoder import InlineTableDict
from toml.encoder import TomlPreserveInlineDictEncoder
from yarl import URL

from ai.backend.common.typed_validators import HostPortPair
from ai.backend.common.types import BinarySize
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))

_base_values_by_type = {
    "string": "...",
    "integer": 0,
    "number": 0.0,
    "boolean": False,
    "array": [],
    "object": {},
}


@dataclass(slots=True)
class FormatterContext:
    hint: str = ""
    annotation: type | None = None


class _InlineTable(dict, InlineTableDict):
    pass


def _wrap_comment(text: str, prefix: str = "", width: int = 80) -> str:
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
                wrapped_lines.append(f"{prefix}# {wrapped_line}")

    return "\n".join(wrapped_lines)


def _dump_toml_scalar(
    value: Any,
    default: Any,
    ctx: FormatterContext | None = None,
) -> str:
    match value:
        case {"$ref": complex_type}:
            type_name = complex_type.removeprefix("#/$defs/").split("__")[-1]
            if default is not None:
                return _dump_toml_scalar(default, None, ctx)
            return _dump_toml_scalar("{ " + type_name + " }", default, ctx)
        case {"type": "array", "items": item_type}:
            if default is not None:
                if isinstance(default, list):
                    return _dump_toml_scalar(default, None, ctx)
                else:
                    return "[ " + _dump_toml_scalar(default, None, ctx) + " ]"
            return "[ " + _dump_toml_scalar(item_type, default, ctx) + " ]"
        case {"type": "integer"} | {"type": "number"}:
            if default is None:
                out = "  "
            else:
                out = _dump_toml_scalar(default, None, ctx)
            has_min = False
            if (min_ := value.get("minimum", None)) is not None:
                out += f"  # min={min_}"
                has_min = True
            if (max_ := value.get("maximum", None)) is not None:
                if not has_min:
                    out += "  #"
                out += f" max={max_}"
            return out
        case {"type": "string", "format": "file-path"} | {"type": "string", "format": "path"}:
            if default is not None:
                return _dump_toml_scalar(default, None, ctx)
            return _dump_toml_scalar("PATH", default)
        case {"type": toml_type}:
            if default is not None:
                return _dump_toml_scalar(default, None, ctx)
            return _dump_toml_scalar(_base_values_by_type[toml_type], default)
        case IPv4Network() | IPv4Address() | IPv6Network() | IPv6Address():
            if default is not None:
                return _dump_toml_scalar(default, None, ctx)
            return str(value)
        case PosixPath() | PurePath() | URL() | timedelta():
            if default is not None:
                return _dump_toml_scalar(default, None, ctx)
            return str(value)
    if default is not None:
        return _dump_toml_scalar(default, None, ctx)
    if ctx is not None:
        match ctx.hint:
            case "BinarySize":
                value = f"{BinarySize(value):s}".upper()
            case "HostPortPair":
                value = {"host": value.host, "port": value.port}
            case "EnumByValue":
                assert ctx.annotation is not None
                value = ctx.annotation(value).value
            case "EnumByName":
                assert ctx.annotation is not None
                value = ctx.annotation(value).name
    if isinstance(value, dict):
        return (
            toml.dumps({"x": _InlineTable(value)}, encoder=TomlPreserveInlineDictEncoder())
            .strip()
            .split(" = ", 1)[1]
        )
    return toml.dumps({"x": value}).strip().split(" = ", 1)[1]


def _generate_sample_config(model_class: Type[BaseModel]) -> str:
    """
    Generate a sample TOML configuration file from a Pydantic model.

    Args:
        model_class: The Pydantic model class to generate configuration for

    Returns:
        A string containing the TOML configuration with comments
    """
    warnings: list[str] = []
    schema = model_class.model_json_schema()

    def _get_field_info(model_cls: Type[BaseModel], field_name: str, indent: int) -> dict[str, Any]:
        """Extract field information from Pydantic model including Field metadata."""
        field_info: dict[str, Any] = {}
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
                field_info["annotation"] = field.annotation

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
                        if isinstance(factory_instance, BaseModel):
                            field_info["default"] = factory_instance.model_dump()
                        else:
                            field_info["default"] = factory_instance
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
        indent: int = 0,
        model_cls: Optional[Type[BaseModel]] = None,
    ) -> list[str]:
        """Process a single property and return TOML lines with comments."""
        lines = []
        indent_str = "  " * indent

        # Get field information from Pydantic model if available
        field_info = {}
        if model_cls:
            field_info = _get_field_info(model_cls, prop_name, indent=indent)

        # Add description as comment if available
        description = field_info.get("description") or prop_schema.get("description")
        if description:
            if "This field is injected at runtime" in description:
                # Skip runtimme-generated fields.
                return []
            comment_lines = _wrap_comment(description)
            for line in comment_lines.split("\n"):
                lines.append(f"{indent_str}{line}")

        # Get the value to use - prioritize Field examples over schema examples
        value = None

        # Transform prop_schema into value expression
        optional = False
        union = False
        default = None
        example = None
        fmt_ctx = FormatterContext()

        if annotation := field_info.get("annotation", None):
            if isinstance(annotation, type):
                fmt_ctx.annotation = annotation
                if issubclass(annotation, BinarySize):
                    fmt_ctx.hint = "BinarySize"
                if issubclass(annotation, HostPortPair):
                    fmt_ctx.hint = "HostPortPair"
                if issubclass(annotation, enum.Enum):
                    if annotation.__name__ in ("AffinityPolicy",):
                        fmt_ctx.hint = "EnumByName"
                    else:
                        fmt_ctx.hint = "EnumByValue"

        match prop_schema:
            case {"anyOf": [v1, v2]}:
                if v1 == {"type": "null"}:
                    # optional value
                    value = v2
                    optional = True
                elif v2 == {"type": "null"}:
                    # optional value
                    value = v1
                    optional = True
                else:
                    # union types
                    value = [v1, v2]
                    union = True
            case {"default": v} if v != PydanticUndefined and v != ...:
                value = v
                default = v
            case _:
                value = _base_values_by_type.get(prop_schema.get("type", "string"), "?")
        if default is None:
            default = field_info.get("default", PydanticUndefined)
            if default is PydanticUndefined:
                default = None
        if (_examples := prop_schema.get("examples", PydanticUndefined)) is not PydanticUndefined:
            if _examples:
                example = _examples[0]
        if (_example := prop_schema.get("example", PydanticUndefined)) is not PydanticUndefined:
            example = _example
        if (_enum := prop_schema.get("enum", PydanticUndefined)) is not PydanticUndefined:
            example = _enum[0]

        # Format the property line
        line = indent_str
        print(
            f"{indent_str}{prop_name} ({optional=}, {union=}, {default=}, {example=}, {annotation=})",
        )
        match value:
            case None:
                # null does not exist in TOML, so just leave it as empty space
                line += f"# {prop_name} ="
            case _ if union:
                assert isinstance(value, Sequence)
                if not optional:
                    line += "## "
                line += f"{prop_name} = "
                line += _dump_toml_scalar(value[0], example, fmt_ctx)
                # Append additional unions as comments
                line += "  # | "
                line += " | ".join(_dump_toml_scalar(v, example, fmt_ctx) for v in value[1:])
            case _:
                if optional:
                    line += "## "
                # The default is likely to be None if optional.
                # Take the example value as the placeholder.
                line += f"{prop_name} = {_dump_toml_scalar(value, example if default is None else default, fmt_ctx)}"

        lines.append(line)
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

            if (prop_type == "object" or "properties" in prop_schema) and prop_schema[
                "title"
            ] != "HostPortPair":
                object_props[prop_name] = prop_schema
            else:
                simple_props[prop_name] = prop_schema

        # Add simple properties first
        processed_simple_props = []
        for prop_name, prop_schema in simple_props.items():
            prop_lines = _process_property(
                prop_name, prop_schema, indent=len(path), model_cls=model_cls
            )
            if prop_lines:
                lines.extend(prop_lines)
                processed_simple_props.append(prop_name)

        if path == [] and processed_simple_props:
            # ref: https://github.com/toml-lang/toml/issues/984
            warnings.append(
                "The configuration schema CANNOT have simple fields in the root "
                "without any section header according to the TOML specification. "
                "Also, optional sections should be defined non-optional with explicit default factory. "
                f"Please move or fix these fields/sections: {', '.join(simple_props.keys())}. "
            )

        # Add object properties as sections
        for prop_name, prop_schema in object_props.items():
            indent_str = "  " * len(path)

            if lines and lines[-1].strip():  # Add blank line before section
                lines.append("")

            # Add section comment
            if "description" in prop_schema:
                comment_lines = _wrap_comment(prop_schema["description"], prefix=indent_str)
                lines.extend(comment_lines.split("\n"))

            # Add section header
            section_path = path + [prop_name]
            section_header = f"{indent_str}[{'.'.join(section_path)}]"
            lines.append(section_header)
            print(section_header)

            # Process nested properties - try to get nested model class
            nested_model_cls = None
            if model_cls and hasattr(model_cls, "model_fields"):
                field_info = _get_field_info(model_cls, prop_name, indent=len(path))
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
    for msg in warnings:
        log.warning(msg)
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
    try:
        config_content = _generate_sample_config(model_class)
    except Exception:
        log.exception("Error while generating sample config schema")
    with open(output_path, "w") as f:
        if header_comment:
            f.write(_wrap_comment(header_comment))
            f.write("\n\n")
        f.write(config_content)
        f.write("\n")
