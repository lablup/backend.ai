from __future__ import annotations

import textwrap

from ..session import api_session
from .base import BaseFunction, api_function

__all__ = ("ContainerRegistry",)


class ContainerRegistry(BaseFunction):
    """
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches, modifies various container registry
    information.

    .. note::

      All methods in this function class require your API access key to
      have the *admin* privilege.
    """

    @api_function
    @classmethod
    async def associate_group(cls, registry_id: str, group_id: str) -> dict:
        """
        Associate container_registry with group.

        :param registry_id: The id of a container registry.
        :param group_id: The id of a group.
        """
        query = textwrap.dedent(
            """\
            mutation($registry_id: String!, $group_id: String!) {
                associate_container_registry_with_group(
                        registry_id: $registry_id, group_id: $group_id) {
                    ok msg
                }
            }
        """
        )
        variables = {"registry_id": registry_id, "group_id": group_id}
        data = await api_session.get().Admin._query(query, variables)
        return data["associate_container_registry_with_group"]

    @api_function
    @classmethod
    async def disassociate_group(cls, registry_id: str, group_id: str) -> dict:
        """
        Disassociate container_registry with group.

        :param registry_id: The id of a container registry.
        :param group_id: The id of a group.
        """
        query = textwrap.dedent(
            """\
            mutation($registry_id: String!, $group_id: String!) {
                disassociate_container_registry_with_group(
                        registry_id: $registry_id, group_id: $group_id) {
                    ok msg
                }
            }
        """
        )
        variables = {"registry_id": registry_id, "group_id": group_id}
        data = await api_session.get().Admin._query(query, variables)
        return data["disassociate_container_registry_with_group"]
