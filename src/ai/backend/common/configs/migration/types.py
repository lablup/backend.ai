from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MappingRule:
    """A rule that maps an existing TOML config field to a service-discovery endpoint."""

    source: str
    role: str
    scope: str
    protocol: str
    fallback: str | None = None


@dataclass
class DetectedField:
    """A field detected from the existing config file."""

    key_path: str
    host: str
    port: int
    is_fallback: bool


@dataclass
class GeneratedEndpoint:
    """An endpoint generated from a detected field."""

    role: str
    scope: str
    address: str
    port: int
    protocol: str
    source_field: DetectedField


@dataclass
class MigrationResult:
    """The result of a config migration run."""

    detected_fields: list[DetectedField]
    generated_endpoints: list[GeneratedEndpoint]
    skipped_rules: list[tuple[MappingRule, str]]
    has_existing_endpoints: bool
