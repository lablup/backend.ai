import textwrap
from io import BytesIO
from typing import Any, Mapping, Optional, Sequence
from uuid import UUID

from faker import Faker

from ai.backend.client.output.fields import session_fields
from ai.backend.client.output.types import FieldSpec, PaginatedResult
from ai.backend.client.pagination import fetch_paginated_result
from ai.backend.client.request import Request
from ai.backend.client.session import api_session

from .base import BaseFunction, api_function

__all__ = ("Service",)

_default_list_fields: Sequence[FieldSpec] = (
    session_fields["session_id"],
    session_fields["image"],
    session_fields["type"],
    session_fields["status"],
    session_fields["status_info"],
    session_fields["status_changed"],
    session_fields["result"],
)

_default_detail_fields: Sequence[FieldSpec] = (
    session_fields["session_id"],
    session_fields["image"],
    session_fields["type"],
    session_fields["status"],
    session_fields["status_info"],
    session_fields["status_changed"],
    session_fields["result"],
)


class Service(BaseFunction):
    id: Optional[UUID]
    name: Optional[str]

    @api_function
    @classmethod
    async def list(cls):
        """ """
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
        """ """
        return await fetch_paginated_result(
            "compute_session_list",
            {
                "session_type": ("INFERENCE", "String"),
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
        service_id: str,
        fields: Sequence[FieldSpec] = _default_detail_fields,
    ) -> Sequence[dict]:
        query = textwrap.dedent(
            """\
            query($service_id: UUID!) {
                compute_session(service_id: $service_id) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {"service_id": service_id}
        data = await api_session.get().Admin._query(query, variables)
        return data["agent"]

    @api_function
    @classmethod
    async def info(cls, service_id: str):
        rqst = Request("GET", "/service/info")
        rqst.set_json(
            {
                "service_id": service_id,
            }
        )
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def create(
        self,
        model_id: str,
        model_version: str,
        image_ref: str,
        resource_opts: Mapping[str, Any],
        project: Optional[str],
        endpoint_id: Optional[str],
        service_name: Optional[str],
        tag: Optional[str] = None,
        scaling_group: Optional[str] = None,
    ):
        if service_name is None:
            faker = Faker()
            service_name = f"bai-serve-{faker.user_name()}"

        rqst = Request("POST", "/service")
        rqst.set_json(
            {
                "tag": tag,
                "config": {
                    "resource_opts": resource_opts,
                    "scaling_group": scaling_group,
                },
                "model_id": model_id,
                "service_name": service_name,
                "model_version": model_version,
                "image_ref": image_ref,
                "resource_opts": resource_opts,
                "endpoint_id": endpoint_id,
            }
        )
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def delete(self, service_id: str):
        rqst = Request("DELETE", "/service")
        rqst.set_json(
            {
                "service_id": service_id,
            }
        )
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def start(self, service_id: str):
        pass

    @api_function
    @classmethod
    async def stop(self, service_id: str):
        pass

    @api_function
    @classmethod
    async def invoke(
        self,
        service_id: str,
        input_args: Mapping[str, Any],
        input_data: Optional[bytes | bytearray | memoryview | BytesIO] = None,
    ):
        rqst = Request("POST", "/service/invoke")
        rqst.set_json(
            {
                "service_id": service_id,
                "input_args": input_args,
            }
        )
        if input_data:
            rqst.set_content(input_data)
        async with rqst.fetch() as resp:
            return await resp.json()
