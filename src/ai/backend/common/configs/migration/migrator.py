from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import tomlkit
from tomlkit.items import AoT, Array
from tomlkit.toml_document import TOMLDocument

from ai.backend.common.configs.service_discovery import ServiceEndpointConfig

from .types import (
    DetectedField,
    GeneratedEndpoint,
    MappingRule,
    MigrationResult,
)


class ConfigMigrator:
    """Migrates legacy TOML config address/port fields to service-discovery endpoints."""

    def __init__(self, rules: Sequence[MappingRule]) -> None:
        self._rules = rules

    @staticmethod
    def extract_field(config: Mapping[str, Any], dotted_key: str) -> tuple[str, int] | None:
        """Extract (host, port) from a dotted key path in a TOML config dict.

        Supports inline table format like ``{ host = "...", port = ... }``.
        Returns ``None`` if the key path does not exist or the value is not
        a host/port pair.
        """
        parts = dotted_key.split(".")
        current: Any = config
        for part in parts:
            if not isinstance(current, Mapping):
                return None
            current = current.get(part)
            if current is None:
                return None
        if isinstance(current, Mapping):
            host = current.get("host")
            port = current.get("port")
            if host is not None and port is not None:
                return str(host), int(port)
        return None

    @staticmethod
    def check_existing_endpoints(config: Mapping[str, Any]) -> bool:
        """Return True if the config already has non-empty service-discovery endpoints."""
        sd = config.get("service-discovery")
        if sd is None:
            return False
        endpoints = sd.get("endpoints")
        if endpoints is None:
            return False
        if isinstance(endpoints, (list, Array, AoT)):
            return len(endpoints) > 0
        return False

    def migrate(self, config: Mapping[str, Any]) -> MigrationResult:
        """Apply all mapping rules and return a MigrationResult."""
        detected: list[DetectedField] = []
        generated: list[GeneratedEndpoint] = []
        skipped: list[tuple[MappingRule, str]] = []
        has_existing = self.check_existing_endpoints(config)

        for rule in self._rules:
            result = self.extract_field(config, rule.source)
            is_fallback = False

            if result is None and rule.fallback is not None:
                result = self.extract_field(config, rule.fallback)
                is_fallback = True

            if result is None:
                reason = f"field not found: {rule.source}"
                if rule.fallback:
                    reason += f" (fallback: {rule.fallback})"
                skipped.append((rule, reason))
                continue

            host, port = result
            key_path = rule.fallback if is_fallback and rule.fallback else rule.source

            field = DetectedField(
                key_path=key_path,
                host=host,
                port=port,
                is_fallback=is_fallback,
            )
            detected.append(field)

            # Validate via Pydantic
            ServiceEndpointConfig(
                role=rule.role,
                scope=rule.scope,
                address=host,
                port=port,
                protocol=rule.protocol,
                metadata={},
            )

            endpoint = GeneratedEndpoint(
                role=rule.role,
                scope=rule.scope,
                address=host,
                port=port,
                protocol=rule.protocol,
                source_field=field,
            )
            generated.append(endpoint)

        return MigrationResult(
            detected_fields=detected,
            generated_endpoints=generated,
            skipped_rules=skipped,
            has_existing_endpoints=has_existing,
        )

    @staticmethod
    def generate_toml_section(result: MigrationResult) -> str:
        """Generate a TOML string for the [service-discovery.endpoints] section."""
        doc = tomlkit.document()

        sd_table = tomlkit.table(is_super_table=True)
        endpoints = tomlkit.aot()

        for ep in result.generated_endpoints:
            item = tomlkit.table()
            item.add("role", ep.role)
            item.add("scope", ep.scope)
            item.add("address", ep.address)
            item.add("port", ep.port)
            item.add("protocol", ep.protocol)
            endpoints.append(item)

        sd_table.add("endpoints", endpoints)
        doc.add("service-discovery", sd_table)

        return tomlkit.dumps(doc)

    @staticmethod
    def format_dry_run_output(result: MigrationResult) -> str:
        """Format a human-readable dry-run output with comments and TOML section."""
        lines: list[str] = []
        lines.append("# Detected fields from existing configuration:")
        for field in result.detected_fields:
            fallback_marker = " (fallback)" if field.is_fallback else ""
            lines.append(f"#   {field.key_path}{fallback_marker} = {field.host}:{field.port}")

        if result.skipped_rules:
            lines.append("#")
            lines.append("# Skipped rules:")
            for rule, reason in result.skipped_rules:
                lines.append(f"#   {rule.role}/{rule.scope}: {reason}")

        lines.append("")

        if result.generated_endpoints:
            lines.append(ConfigMigrator.generate_toml_section(result))
        else:
            lines.append("# No endpoints were generated.")

        return "\n".join(lines)

    @staticmethod
    def append_to_document(doc: TOMLDocument, result: MigrationResult) -> TOMLDocument:
        """Append generated endpoints into an existing tomlkit document."""
        sd = doc.get("service-discovery")
        if sd is None:
            sd = tomlkit.table(is_super_table=True)
            doc.add("service-discovery", sd)

        endpoints = tomlkit.aot()
        for ep in result.generated_endpoints:
            item = tomlkit.table()
            item.add("role", ep.role)
            item.add("scope", ep.scope)
            item.add("address", ep.address)
            item.add("port", ep.port)
            item.add("protocol", ep.protocol)
            endpoints.append(item)

        sd.add("endpoints", endpoints)
        return doc
