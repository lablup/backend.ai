from __future__ import annotations

from ai.backend.common.configs.migration.types import MappingRule

WORKER_MAPPING_RULES: list[MappingRule] = [
    MappingRule(
        source="proxy_worker.announce_addr",
        fallback="proxy_worker.api_advertised_addr",
        role="api",
        scope="cluster",
        protocol="http",
    ),
]
