from __future__ import annotations

from ai.backend.common.configs.migration.types import MappingRule

STORAGE_MAPPING_RULES: list[MappingRule] = [
    MappingRule(
        source="api.manager.announce-addr",
        fallback="api.manager.service-addr",
        role="api",
        scope="cluster",
        protocol="http",
    ),
    MappingRule(
        source="api.client.service-addr",
        role="client-api",
        scope="cluster",
        protocol="http",
    ),
    MappingRule(
        source="api.manager.announce-internal-addr",
        fallback="api.manager.internal-addr",
        role="client-api",
        scope="container",
        protocol="http",
    ),
]
