from __future__ import annotations

from ai.backend.common.configs.migration.types import MappingRule

MANAGER_MAPPING_RULES: list[MappingRule] = [
    MappingRule(
        source="manager.service-addr",
        role="api",
        scope="cluster",
        protocol="http",
    ),
]
