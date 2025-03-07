from __future__ import annotations

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    MutableMapping,
    Optional,
    Self,
)

import graphene

from ai.backend.manager.models.base import privileged_mutation
from ai.backend.manager.models.user import UserRole

from ...gql_relay import AsyncNode

if TYPE_CHECKING:
    from ai.backend.manager.models.gql import GraphQueryContext

from ai.backend.common.types import AgentId

__all__ = ("AbusingReportConfig",)


class AbusingReportConfig(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 25.5.0."

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


class ModifyAbusingReportConfigInput(graphene.InputObjectType):
    abuse_report_path = graphene.String()
    force_terminate_abusing_containers = graphene.Boolean()

    class Meta:
        description = "Added in 25.5.0."


class ModifyAbusingReportConfig(graphene.Mutation):
    """Added in 25.5.0."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        agent_id = graphene.String(required=True)
        props = ModifyAbusingReportConfigInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    @privileged_mutation(
        UserRole.SUPERADMIN,
        lambda id, **kwargs: (None, id),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        agent_id: AgentId,
        props: ModifyAbusingReportConfigInput,
    ) -> Self:
        graph_ctx: GraphQueryContext = info.context

        data: MutableMapping[str, Any] = {}
        if props.abuse_report_path:
            data["abuse-report-path"] = Path(props.abuse_report_path)
        if props.force_terminate_abusing_containers:
            data["force-terminate-abusing-containers"] = props.force_terminate_abusing_containers

        try:
            await graph_ctx.registry.set_agent_local_config(agent_id, {"agent": data})
        except Exception as e:
            return cls(ok=False, msg=str(e))

        return cls(ok=True, msg="")
