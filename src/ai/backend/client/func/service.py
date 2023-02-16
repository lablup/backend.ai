import textwrap
from typing import Any, Mapping, Sequence
from uuid import UUID

from ai.backend.client.output.types import FieldSpec, PaginatedResult
from ai.backend.client.pagination import fetch_paginated_result
from ai.backend.client.request import Request
from ai.backend.client.session import api_session

from .base import BaseFunction, api_function

__all__ = ("Service",)

_default_list_fields: Sequence[FieldSpec] = tuple()

_default_detail_fields: Sequence[FieldSpec] = tuple()


class Service(BaseFunction):
    endpoint_id: str

    def __init__(self, endpoint_id: UUID):
        self.endpoint_id = str(endpoint_id)

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
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult:
        """ """
        return await fetch_paginated_result(
            "serve_list",
            {
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
        endpoint_id: str,
        fields: Sequence[FieldSpec] = _default_detail_fields,
    ) -> Sequence[dict]:
        query = textwrap.dedent(
            """\
            query($endpoint_id: UUID!) {
                endpoint(endpoint_id: $endpoint_id) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {"endpoint_id": endpoint_id}
        data = await api_session.get().Admin._query(query, variables)
        return data["agent"]

    @api_function
    async def info(self):
        rqst = Request("GET", "/serves/{0}".format(self.endpoint_id))
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def create(
        self,
        model_id: str,
        model_version: str,
        image_ref: str,
        project: str,
        resource_opts: Mapping[str, Any],
    ):
        pass

    @api_function
    async def start(self):
        pass

    @api_function
    async def stop(self):
        pass

    @api_function
    async def delete(self):
        pass

    @api_function
    async def invoke(
        self,
        input_args: Mapping[str, Any],
    ):
        pass
