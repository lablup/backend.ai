from __future__ import annotations

from ai.backend.common.configs.migration.types import MappingRule

AGENT_MAPPING_RULES: list[MappingRule] = [
    MappingRule(
        source="agent.advertised-rpc-addr",
        fallback="agent.rpc-listen-addr",
        role="rpc",
        scope="cluster",
        protocol="zmq",
    ),
    MappingRule(
        source="agent.announce-internal-addr",
        fallback="agent.service-addr",
        role="metrics",
        scope="cluster",
        protocol="http",
    ),
    MappingRule(
        source="agent.announce-internal-addr",
        role="metrics",
        scope="container",
        protocol="http",
    ),
]
