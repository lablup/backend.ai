from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest
from aiohttp import web

from ai.backend.common.openapi import OpenAPIDocumentInfo, OpenAPISpecGenerator
from ai.backend.common.types import BackendAISchema


class _ItemResponseModel(BackendAISchema):
    name: str


async def _get_item(_request: web.Request) -> _ItemResponseModel:
    return _ItemResponseModel(name="item")


async def _list_items(_request: web.Request) -> list[_ItemResponseModel]:
    return []


async def _get_plain_response(_request: web.Request) -> web.Response:
    return web.Response()


class _GeneratorWithoutPreconditions(OpenAPISpecGenerator):
    def __init__(self) -> None:
        super().__init__(
            OpenAPIDocumentInfo(
                title="Test API",
                description="Test API specification",
                version="0.0.0",
                security_scheme_name="TestAuth",
                security_scheme={"type": "http", "scheme": "bearer"},
            )
        )

    @override
    def _describe_preconditions(self, handler_attrs: Mapping[str, Any]) -> list[str]:
        return []


@dataclass(frozen=True)
class _ResponseCase:
    handler: Callable[[web.Request], Awaitable[Any]]
    expected_response: dict[str, Any]
    expected_schema_names: frozenset[str]


@dataclass(frozen=True)
class _ItemsOperation:
    operation: dict[str, Any]
    schema_names: frozenset[str]


class TestOpenAPISpecGenerator:
    @pytest.fixture
    def items_operation_of_handler(
        self, handler: Callable[[web.Request], Awaitable[Any]]
    ) -> _ItemsOperation:
        app = web.Application()
        app["prefix"] = "items"
        app.router.add_get("", handler)
        spec = _GeneratorWithoutPreconditions().generate([app])
        return _ItemsOperation(
            operation=spec["paths"]["/items"]["get"],
            schema_names=frozenset(spec["components"]["schemas"]),
        )

    @pytest.fixture
    def handler(self, case: _ResponseCase) -> Callable[[web.Request], Awaitable[Any]]:
        return case.handler

    @pytest.mark.parametrize(
        "case",
        [
            _ResponseCase(
                handler=_get_item,
                expected_response={
                    "description": "",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/_ItemResponseModel"}
                        }
                    },
                },
                expected_schema_names=frozenset({"_ItemResponseModel"}),
            ),
            _ResponseCase(
                handler=_list_items,
                expected_response={
                    "description": "",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/_ItemResponseModel_List"}
                        }
                    },
                },
                expected_schema_names=frozenset({"_ItemResponseModel", "_ItemResponseModel_List"}),
            ),
            _ResponseCase(
                handler=_get_plain_response,
                expected_response={"description": "Successful response"},
                expected_schema_names=frozenset(),
            ),
        ],
        ids=lambda case: case.handler.__name__,
    )
    def test_response_follows_the_return_annotation(
        self, items_operation_of_handler: _ItemsOperation, case: _ResponseCase
    ) -> None:
        assert items_operation_of_handler.operation["responses"] == {"200": case.expected_response}
        assert items_operation_of_handler.schema_names == case.expected_schema_names
