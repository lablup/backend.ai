from typing import Optional, Sequence
from uuid import UUID

from ai.backend.client.output.fields import endpoint_fields
from ai.backend.client.output.types import FieldSpec, PaginatedResult
from ai.backend.client.pagination import fetch_paginated_result
from ai.backend.client.request import Request

from .base import BaseFunction, api_function

__all__ = ("Endpoint",)

_default_list_fields: Sequence[FieldSpec] = (
    endpoint_fields["id"],
    endpoint_fields["image"],
    endpoint_fields["model_id"],
    endpoint_fields["domain_name"],
    endpoint_fields["project_id"],
    endpoint_fields["resource_group_name"],
    endpoint_fields["url"],
)


class Endpoint(BaseFunction):
    id: Optional[UUID]

    @api_function
    @classmethod
    async def list(cls):
        rqst = Request("GET", "/service")
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> PaginatedResult:
        return await fetch_paginated_result(
            "endpoint_list",
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
    async def create(
        self,
        image_ref: str,
        url: str,
        domain_name: Optional[str],
        project_name: Optional[str],
        resource_slots: Optional[str] = None,
        resource_group: Optional[str] = None,
    ):
        rqst = Request("POST", "/endpoint")
        rqst.set_json(
            {
                "url": url,
                "domain_name": domain_name,
                "project_name": project_name,
                "image_ref": image_ref,
                "resource_slots": resource_slots,
                "resource_group": resource_group,
            }
        )
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def delete(self, endpoint_id: str):
        rqst = Request("DELETE", "/endpoint")
        rqst.set_json(
            {
                "endpoint_id": endpoint_id,
            }
        )
        async with rqst.fetch() as resp:
            return await resp.json()
