from __future__ import annotations

from ai.backend.common.configs.migration.types import MappingRule

COORDINATOR_MAPPING_RULES: list[MappingRule] = [
    MappingRule(
        source="proxy_coordinator.announce_addr",
        fallback="proxy_coordinator.advertised_addr",
        role="api",
        scope="cluster",
        protocol="http",
    ),
]
