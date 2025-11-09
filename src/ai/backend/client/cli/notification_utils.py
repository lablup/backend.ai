"""Utility functions for notification CLI commands."""

from __future__ import annotations

from typing import Any


def print_notification_schema(
    schema: dict[str, Any],
    *,
    indent: int = 2,
) -> None:
    """
    Print notification schema in a human-readable format.

    Displays required fields first, then optional fields, with descriptions.

    Args:
        schema: JSON schema dictionary from Pydantic model
        indent: Number of spaces for indentation (default: 2)
    """
    if "properties" not in schema:
        return

    properties = schema["properties"]
    required_fields = schema.get("required", [])

    # Separate required and optional fields
    required_props = {name: info for name, info in properties.items() if name in required_fields}
    optional_props = {
        name: info for name, info in properties.items() if name not in required_fields
    }

    indent_str = " " * indent

    # Display required fields first
    if required_props:
        print(f"{indent_str}Required fields:")
        for field_name, field_info in required_props.items():
            field_type = field_info.get("type", "any")
            description = field_info.get("description", "")

            print(f"{indent_str}  [✓] {field_name}: {field_type}")
            if description:
                # Wrap description if too long
                max_width = 70
                if len(description) > max_width:
                    description = description[: max_width - 3] + "..."
                print(f"{indent_str}      {description}")

    # Display optional fields
    if optional_props:
        if required_props:
            print()  # Empty line between required and optional
        print(f"{indent_str}Optional fields:")
        for field_name, field_info in optional_props.items():
            field_type = field_info.get("type", "any")
            description = field_info.get("description", "")

            print(f"{indent_str}  [ ] {field_name}: {field_type}")
            if description:
                # Wrap description if too long
                max_width = 70
                if len(description) > max_width:
                    description = description[: max_width - 3] + "..."
                print(f"{indent_str}      {description}")
