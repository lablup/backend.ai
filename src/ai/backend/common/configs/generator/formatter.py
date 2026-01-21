from __future__ import annotations

import enum
import json
from collections.abc import Sequence
from datetime import timedelta
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from pathlib import Path, PosixPath, PurePath
from typing import TYPE_CHECKING, Any, Protocol

from .types import FormattedValue

if TYPE_CHECKING:
    from ai.backend.common.configs.inspector import FieldSchema

__all__ = (
    "ValueFormatter",
    "DefaultFormatter",
    "BinarySizeFormatter",
    "HostPortPairFormatter",
    "EnumFormatter",
    "CompositeFormatter",
    "create_default_formatter",
)


class ValueFormatter(Protocol):
    """Protocol for value formatters.

    Formatters convert Python values to TOML-compatible string representations.
    Each formatter handles specific types and returns FormattedValue with
    the formatted string and optional inline comments.
    """

    def can_format(self, type_name: str, value: Any) -> bool:
        """Check if this formatter can handle the given type.

        Args:
            type_name: The type name from FieldSchema.type_info.type_name.
            value: The actual value to format.

        Returns:
            True if this formatter can handle the type.
        """
        ...

    def format(self, value: Any, field: FieldSchema) -> FormattedValue:
        """Format the value for TOML output.

        Args:
            value: The value to format.
            field: The field schema containing type and metadata.

        Returns:
            FormattedValue with the TOML string and optional comment.
        """
        ...


class DefaultFormatter:
    """Default formatter for basic Python types.

    Handles str, int, float, bool, None, list, dict and converts them
    to TOML-compatible string representations.
    """

    def can_format(self, type_name: str, value: Any) -> bool:
        # Default formatter is the fallback, always returns True
        return True

    def format(self, value: Any, field: FieldSchema) -> FormattedValue:
        if value is None:
            # Generate type-based placeholder
            formatted = self._get_type_placeholder(field.type_info.type_name)
        else:
            formatted = self._format_value(value)
        return FormattedValue(value=formatted)

    def _get_type_placeholder(self, type_name: str) -> str:
        """Get placeholder value based on type name."""
        type_lower = type_name.lower()

        if "path" in type_lower:
            return '"/path/to/file"'
        if "list" in type_lower or "sequence" in type_lower:
            return "[]"
        if "dict" in type_lower or "mapping" in type_lower:
            return "{}"
        if "int" in type_lower:
            return "0"
        if "float" in type_lower:
            return "0.0"
        if "bool" in type_lower:
            return "false"
        # Default to empty string for str and unknown types
        return '"..."'

    def _format_value(self, value: Any) -> str:
        """Convert a Python value to TOML string representation."""
        match value:
            case None:
                # Should not reach here if format() handles None
                return '"..."'
            case bool():
                return "true" if value else "false"
            case int() | float():
                return str(value)
            case str():
                # Escape and quote strings
                return self._quote_string(value)
            case list():
                if not value:
                    return "[]"
                items = [self._format_value(item) for item in value]
                return f"[{', '.join(items)}]"
            case dict():
                if not value:
                    return "{}"
                pairs = [f"{k} = {self._format_value(v)}" for k, v in value.items()]
                return "{ " + ", ".join(pairs) + " }"
            case Path() | PosixPath() | PurePath():
                return self._quote_string(str(value))
            case timedelta():
                # Format as seconds or human-readable
                total_seconds = int(value.total_seconds())
                return str(total_seconds)
            case IPv4Address() | IPv6Address():
                return self._quote_string(str(value))
            case IPv4Network() | IPv6Network():
                return self._quote_string(str(value))
            case _:
                # Fallback: convert to string and quote
                return self._quote_string(str(value))

    def _quote_string(self, s: str) -> str:
        """Quote a string for TOML, handling escapes."""
        # Use json.dumps for proper escaping, then it's valid TOML
        return json.dumps(s)


class BinarySizeFormatter:
    """Formatter for BinarySize values.

    Converts byte sizes to human-readable format (e.g., "1G", "512M").
    """

    _UNITS = ["B", "K", "M", "G", "T", "P"]

    def can_format(self, type_name: str, value: Any) -> bool:
        return "BinarySize" in type_name

    def format(self, value: Any, field: FieldSchema) -> FormattedValue:
        formatted = self._format_binary_size(value)
        return FormattedValue(value=f'"{formatted}"')

    def _format_binary_size(self, value: Any) -> str:
        """Convert bytes to human-readable size string."""
        if value is None:
            # Default placeholder for BinarySize
            return "0B"
        if isinstance(value, str):
            # Already formatted (e.g., "1G")
            return value.upper()

        try:
            bytes_val: float = float(value)
        except (ValueError, TypeError):
            return str(value)

        if bytes_val == 0:
            return "0B"

        for unit in self._UNITS:
            if bytes_val < 1024 or unit == "P":
                if bytes_val == int(bytes_val):
                    return f"{int(bytes_val)}{unit}"
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024

        return str(value)


class HostPortPairFormatter:
    """Formatter for HostPortPair values.

    Formats as inline table: { host = "...", port = ... }
    """

    def can_format(self, type_name: str, value: Any) -> bool:
        return "HostPortPair" in type_name

    def format(self, value: Any, field: FieldSchema) -> FormattedValue:
        formatted = self._format_host_port(value)
        return FormattedValue(value=formatted)

    def _format_host_port(self, value: Any) -> str:
        """Format HostPortPair as TOML inline table."""
        if value is None:
            # Default placeholder for HostPortPair
            return '{ host = "localhost", port = 0 }'
        if isinstance(value, dict):
            host = value.get("host", "localhost")
            port = value.get("port", 0)
        elif isinstance(value, str):
            # Parse "host:port" format
            if ":" in value:
                parts = value.rsplit(":", 1)
                host = parts[0]
                try:
                    port = int(parts[1])
                except ValueError:
                    port = 0
            else:
                host = value
                port = 0
        elif hasattr(value, "host") and hasattr(value, "port"):
            host = value.host
            port = value.port
        else:
            return '{ host = "localhost", port = 0 }'

        return f'{{ host = "{host}", port = {port} }}'


class EnumFormatter:
    """Formatter for Enum values.

    Converts enum members to their value representation.
    """

    def can_format(self, type_name: str, value: Any) -> bool:
        return isinstance(value, enum.Enum)

    def format(self, value: Any, field: FieldSchema) -> FormattedValue:
        if isinstance(value, enum.Enum):
            enum_value = value.value
        else:
            enum_value = value

        # Quote string values, leave numbers as-is
        if isinstance(enum_value, str):
            formatted = json.dumps(enum_value)
        else:
            formatted = str(enum_value)

        return FormattedValue(value=formatted)


class SequenceFormatter:
    """Formatter for sequence types (list, tuple).

    Handles arrays with proper TOML formatting.
    """

    def __init__(self, item_formatter: ValueFormatter | None = None) -> None:
        self._item_formatter = item_formatter or DefaultFormatter()

    def can_format(self, type_name: str, value: Any) -> bool:
        return isinstance(value, Sequence) and not isinstance(value, str)

    def format(self, value: Any, field: FieldSchema) -> FormattedValue:
        if not value:
            return FormattedValue(value="[]")

        # For simple types, format inline
        items = []
        for item in value:
            if isinstance(item, str):
                items.append(json.dumps(item))
            elif isinstance(item, bool):
                items.append("true" if item else "false")
            elif isinstance(item, (int, float)):
                items.append(str(item))
            else:
                items.append(json.dumps(str(item)))

        return FormattedValue(value=f"[{', '.join(items)}]")


class CompositeFormatter:
    """Composite formatter that delegates to specialized formatters.

    Tries each formatter in order and uses the first one that can handle
    the given type. Falls back to DefaultFormatter if none match.
    """

    def __init__(self, formatters: Sequence[ValueFormatter] | None = None) -> None:
        """Initialize with a list of formatters.

        Args:
            formatters: Ordered list of formatters to try.
                If None, uses default set of formatters.
        """
        if formatters is None:
            formatters = [
                BinarySizeFormatter(),
                HostPortPairFormatter(),
                EnumFormatter(),
                SequenceFormatter(),
                DefaultFormatter(),
            ]
        self._formatters = list(formatters)
        self._default = DefaultFormatter()

    def can_format(self, type_name: str, value: Any) -> bool:
        return True  # Composite formatter handles everything

    def format(self, value: Any, field: FieldSchema) -> FormattedValue:
        """Format value using the first matching formatter.

        Args:
            value: The value to format.
            field: The field schema.

        Returns:
            FormattedValue from the first matching formatter.
        """
        type_name = field.type_info.type_name

        for formatter in self._formatters:
            if formatter.can_format(type_name, value):
                return formatter.format(value, field)

        # Fallback to default
        return self._default.format(value, field)


def create_default_formatter() -> CompositeFormatter:
    """Create a CompositeFormatter with all default formatters.

    Returns:
        A CompositeFormatter configured with standard formatters for
        BinarySize, HostPortPair, Enum, sequences, and basic types.
    """
    return CompositeFormatter([
        BinarySizeFormatter(),
        HostPortPairFormatter(),
        EnumFormatter(),
        SequenceFormatter(),
        DefaultFormatter(),
    ])
