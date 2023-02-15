from typing import Sequence
from uuid import UUID

from ai.backend.client.output.fields import vfolder_fields
from ai.backend.client.output.types import FieldSpec, PaginatedResult
from ai.backend.client.pagination import fetch_paginated_result
from ai.backend.client.request import Request

from .base import BaseFunction, api_function

__all__ = ("Model",)

_default_list_fields: Sequence[FieldSpec] = (
    vfolder_fields["id"],
    vfolder_fields["name"],
    vfolder_fields["created_at"],
    vfolder_fields["status"],
)


class Model(BaseFunction):
    model_name: str

    def __init__(self, model_name: UUID):
        self.model_name = str(model_name)

    @api_function
    @classmethod
    async def list(cls):
        """ """

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter_: str = None,
        order: str = None,
    ) -> PaginatedResult:
        """ """
        return await fetch_paginated_result(
            "vfolder_list",
            {
                "filter": (filter_, "String"),
                "order": (order, "String"),
            },
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    @api_function
    async def info(self):
        rqst = Request("GET", "/folders/{0}".format(self.model_name))
        async with rqst.fetch() as resp:
            return await resp.json()

    @classmethod
    async def create(
        cls,
        name: str,
        host: str = None,
        unmanaged_path: str = None,
        group: str = None,
        permission: str = "rw",
        quota: str = "0",
        cloneable: bool = False,
    ):
        rqst = Request("POST", "/folders")
        rqst.set_json(
            {
                "name": name,
                "host": host,
                "unmanaged_path": unmanaged_path,
                "group": group,
                "usage_mode": "model",
                "permission": permission,
                "quota": quota,
                "cloneable": cloneable,
            }
        )
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete(self):
        rqst = Request("DELETE", "/folders")
        rqst.set_json({"id": self.model_name})
        async with rqst.fetch():
            return {}
