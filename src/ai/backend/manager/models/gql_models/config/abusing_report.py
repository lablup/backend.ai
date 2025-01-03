from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Optional,
    Self,
)

import graphene

from ...gql_relay import AsyncNode

if TYPE_CHECKING:
    from ai.backend.manager.models.gql import GraphQueryContext

from ai.backend.common.types import AgentId

if TYPE_CHECKING:
    pass

__all__ = ("AbusingReportConfig",)


class AbusingReportConfig(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 25.1.0."

    abuse_report_path = graphene.String()
    force_terminate_abusing_containers = graphene.Boolean()

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, agent_id: AgentId) -> Optional[Self]:
        graph_ctx: GraphQueryContext = info.context
        agent_local_config = await graph_ctx.registry.get_agent_local_config(agent_id)
        if agent_local_config is None or "agent" not in agent_local_config:
            return None

        return cls(
            abuse_report_path=agent_local_config["agent"].get("abuse-report-path"),
            force_terminate_abusing_containers=agent_local_config["agent"].get(
                "force-terminate-abusing-containers"
            ),
        )
