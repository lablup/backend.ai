from typing import Sequence
from uuid import UUID

from ..output.fields import network_fields
from ..output.types import FieldSpec, RelayPaginatedResult
from ..pagination import execute_paginated_relay_query
from ..session import api_session
from ..utils import dedent as _d
from .base import BaseFunction, api_function

__all__ = ("Network",)

_default_list_fields = (
    network_fields["name"],
    network_fields["ref_name"],
    network_fields["driver"],
    network_fields["created_at"],
)


class Network(BaseFunction):
    @api_function
    @classmethod
    async def paginated_list(
        cls,
        *,
        fields: Sequence[FieldSpec] | None = None,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str | None = None,
        order: str | None = None,
    ) -> RelayPaginatedResult[dict]:
        """
        Fetches the list of created networks in this cluster.
        """
        return await execute_paginated_relay_query(
            "networks",
            {
                "filter": (filter, "String"),
                "order": (order, "String"),
            },
            fields or _default_list_fields,
            limit=page_size,
            offset=page_offset,
        )

    @api_function
    @classmethod
    async def create(
        cls,
        project_id: str,
        name: str,
        *,
        driver: str | None = None,
    ) -> "Network":
        """
        Creates a new network.
        :param project_id: The ID of the project to which the network belongs.
        :param name: The name of the network.
        :param driver: (Optional) The driver of the network. If not specified, the default driver will be used.
        :return: The created network.
        """
        q = _d("""
            mutation($name: String!, $project_id: UUID!, $driver: String) {
                create_network(name: $name, project_id: $project_id, driver: $driver) {
                    network { row_id }
                }
            }
        """)
        data = await api_session.get().Admin._query(
            q,
            {
                "name": name,
                "project_id": project_id,
                "driver": driver,
            },
        )
        return cls(network_id=UUID(data["create_network"]["network"]["row_id"]))

    def __init__(self, network_id: UUID) -> None:
        """
        :param network_id: The ID of the network. Pass `row_id` value (not `id`) of the network info fetched by `paginated_list`.
        """
        super().__init__()
        self.network_id = network_id

    @api_function
    async def get(
        self,
        fields: Sequence[FieldSpec] | None = None,
    ) -> dict:
        """
        Fetches the information of the network.
        """
        q = _d("""
            query($id: String!) {
                network(id: $id) { $fields }
            }
        """)
        q = q.replace("$fields", " ".join(f.field_ref for f in (fields or _default_list_fields)))
        data = await api_session.get().Admin._query(q, {"id": str(self.network_id)})
        return data["images"]

    @api_function
    async def update(self, name: str) -> None:
        """
        Updates network.
        """
        q = _d("""
            mutation($network: String!, $props: UpdateNetworkInput!) {
                modify_network(network: $network, props: $props) {
                   ok msg
                }
            }
        """)
        variables = {
            "network": str(self.network_id),
            "props": {"name": name},
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["modify_network"]

    @api_function
    async def delete(self) -> None:
        """
        Deletes network. Delete only works for networks that are not attached to active session.
        """
        q = _d("""
            mutation($network: String!) {
                delete_network(network: $network) {
                    ok msg
                }
            }
        """)
        variables = {
            "network": str(self.network_id),
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["delete_network"]
