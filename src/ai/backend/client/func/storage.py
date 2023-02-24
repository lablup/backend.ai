import textwrap
from typing import Sequence

from ai.backend.client.output.fields import storage_fields
from ai.backend.client.output.types import FieldSpec, PaginatedResult
from ai.backend.client.pagination import fetch_paginated_result
from ai.backend.client.session import api_session

from .base import BaseFunction, api_function

__all__ = ("Storage",)

_default_list_fields = (
    storage_fields["id"],
    storage_fields["backend"],
    storage_fields["capabilities"],
)

_default_detail_fields = (
    storage_fields["id"],
    storage_fields["backend"],
    storage_fields["path"],
    storage_fields["fsprefix"],
    storage_fields["capabilities"],
    storage_fields["hardware_metadata"],
)


class Storage(BaseFunction):
    """
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches various storage volume
    information keyed by vfolder hosts.

    .. note::

      All methods in this function class require your API access key to
      have the *super-admin* privilege.
    """

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        status: str = "ALIVE",
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult[dict]:
        """
        Lists the keypairs.
        You need an admin privilege for this operation.
        """
        return await fetch_paginated_result(
            "storage_volume_list",
            {
                "filter": (filter, "String"),
                "order": (order, "String"),
            },
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    @api_function
    @classmethod
    async def detail(
        cls,
        vfolder_host: str,
        fields: Sequence[FieldSpec] = _default_detail_fields,
    ) -> dict:
        query = textwrap.dedent(
            """\
            query($vfolder_host: String!) {
                storage_volume(id: $vfolder_host) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {"vfolder_host": vfolder_host}
        data = await api_session.get().Admin._query(query, variables)
        return data["storage_volume"]
