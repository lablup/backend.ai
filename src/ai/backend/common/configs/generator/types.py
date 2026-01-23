from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = (
    "FieldVisibility",
    "FormattedValue",
    "GeneratorConfig",
)


class FieldVisibility(StrEnum):
    """Field display mode in generated TOML output."""

    REQUIRED = "required"
    """Field is required and shown as: field = value"""

    OPTIONAL = "optional"
    """Field is optional and shown commented: ## field = value"""

    HIDDEN = "hidden"
    """Field is hidden from output (e.g., runtime-injected fields)"""


@dataclass(frozen=True)
class FormattedValue:
    """A formatted value ready for TOML output.

    Contains the formatted string representation of a value
    along with optional inline comment for additional context.
    """

    value: str
    """The TOML-formatted value string."""

    comment: str | None = None
    """Optional inline comment (e.g., '# min=0, max=100')."""


@dataclass(frozen=True)
class GeneratorConfig:
    """Configuration options for TOML generation.

    Controls formatting, visibility, and output behavior
    of the TOML generator.
    """

    comment_width: int = 80
    """Maximum width for comment line wrapping."""

    indent_size: int = 2
    """Number of spaces per indentation level."""

    show_deprecated: bool = False
    """Whether to include deprecated fields in output."""

    mask_secrets: bool = True
    """Whether to mask secret field values with placeholder."""

    secret_placeholder: str = "***SECRET***"
    """Placeholder text for masked secret values."""

    include_version_comments: bool = False
    """Whether to add version info comments (e.g., '# Added in 25.1.0')."""
