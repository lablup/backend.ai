from __future__ import annotations

import textwrap
from typing import Sequence

from ai.backend.client.output.fields import agent_fields
from ai.backend.client.output.types import FieldSpec, PaginatedResult
from ai.backend.client.pagination import fetch_paginated_result
from ai.backend.client.request import Request
from ai.backend.client.session import api_session

from .base import BaseFunction, api_function

__all__ = (
    "Agent",
    "AgentWatcher",
)

_default_list_fields = (
    agent_fields["id"],
    agent_fields["status"],
    agent_fields["scaling_group"],
    agent_fields["available_slots"],
    agent_fields["occupied_slots"],
)

_default_detail_fields = (
    agent_fields["id"],
    agent_fields["status"],
    agent_fields["scaling_group"],
    agent_fields["addr"],
    agent_fields["region"],
    agent_fields["first_contact"],
    agent_fields["cpu_cur_pct"],
    agent_fields["mem_cur_bytes"],
    agent_fields["available_slots"],
    agent_fields["occupied_slots"],
    agent_fields["local_config"],
)


class Agent(BaseFunction):
    """
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches various agent
    information.

    .. note::

      All methods in this function class require your API access key to
      have the *admin* privilege.
    """

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        status: str = "ALIVE",
        scaling_group: str = None,
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult:
        """
        Lists the keypairs.
        You need an admin privilege for this operation.
        """
        return await fetch_paginated_result(
            "agent_list",
            {
                "status": (status, "String"),
                "scaling_group": (scaling_group, "String"),
                "filter": (filter, "String"),
                "order": (order, "String"),
            },
            fields,
            page_size=page_size,
            page_offset=page_offset,
        )

    @api_function
    @classmethod
    async def detail(
        cls,
        agent_id: str,
        fields: Sequence[FieldSpec] = _default_detail_fields,
    ) -> Sequence[dict]:
        query = textwrap.dedent(
            """\
            query($agent_id: String!) {
                agent(agent_id: $agent_id) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {"agent_id": agent_id}
        data = await api_session.get().Admin._query(query, variables)
        return data["agent"]


class AgentWatcher(BaseFunction):
    """
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that manipulate agent status.

    .. note::

      All methods in this function class require you to
      have the *superadmin* privilege.
    """

    @api_function
    @classmethod
    async def get_status(cls, agent_id: str) -> dict:
        """
        Get agent and watcher status.
        """
        rqst = Request("GET", "/resource/watcher")
        rqst.set_json({"agent_id": agent_id})
        async with rqst.fetch() as resp:
            data = await resp.json()
            if "message" in data:
                return data["message"]
            else:
                return data

    @api_function
    @classmethod
    async def agent_start(cls, agent_id: str) -> dict:
        """
        Start agent.
        """
        rqst = Request("POST", "/resource/watcher/agent/start")
        rqst.set_json({"agent_id": agent_id})
        async with rqst.fetch() as resp:
            data = await resp.json()
            if "message" in data:
                return data["message"]
            else:
                return data

    @api_function
    @classmethod
    async def agent_stop(cls, agent_id: str) -> dict:
        """
        Stop agent.
        """
        rqst = Request("POST", "/resource/watcher/agent/stop")
        rqst.set_json({"agent_id": agent_id})
        async with rqst.fetch() as resp:
            data = await resp.json()
            if "message" in data:
                return data["message"]
            else:
                return data

    @api_function
    @classmethod
    async def agent_restart(cls, agent_id: str) -> dict:
        """
        Restart agent.
        """
        rqst = Request("POST", "/resource/watcher/agent/restart")
        rqst.set_json({"agent_id": agent_id})
        async with rqst.fetch() as resp:
            data = await resp.json()
            if "message" in data:
                return data["message"]
            else:
                return data
