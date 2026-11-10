from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import click
import pytest
from aiohttp import web
from click.testing import CliRunner

from ai.backend.appproxy.common.openapi import generate_openapi
from ai.backend.appproxy.common.types import PydanticResponse
from ai.backend.appproxy.coordinator.cli.__main__ import main as coordinator_cli
from ai.backend.appproxy.worker.cli.__main__ import main as worker_cli
from ai.backend.common.types import BackendAISchema

_ITEM_SCHEMA_REF = "#/components/schemas/_ItemResponseModel"


class _ItemResponseModel(BackendAISchema):
    name: str


async def _list_items(_request: web.Request) -> PydanticResponse[list[_ItemResponseModel]]:
    return PydanticResponse([])


async def _get_item(_request: web.Request) -> PydanticResponse[_ItemResponseModel]:
    return PydanticResponse(_ItemResponseModel(name="item"))


async def _get_item_or_plain_response(
    _request: web.Request,
) -> PydanticResponse[_ItemResponseModel] | web.Response:
    return web.Response()


@dataclass(frozen=True)
class _ResponseSchemaCase:
    handler: Callable[[web.Request], Awaitable[Any]]
    expected_schema: dict[str, Any]


class TestGenerateOpenAPIResponseSchema:
    @pytest.fixture
    def app_serving_handler_of_case(self, case: _ResponseSchemaCase) -> web.Application:
        app = web.Application()
        app["prefix"] = "items"
        app.router.add_get("", case.handler)
        return app

    @pytest.mark.parametrize(
        "case",
        [
            _ResponseSchemaCase(
                handler=_list_items,
                expected_schema={"type": "array", "items": {"$ref": _ITEM_SCHEMA_REF}},
            ),
            _ResponseSchemaCase(
                handler=_get_item,
                expected_schema={"$ref": _ITEM_SCHEMA_REF},
            ),
            _ResponseSchemaCase(
                handler=_get_item_or_plain_response,
                expected_schema={"$ref": _ITEM_SCHEMA_REF},
            ),
        ],
        ids=lambda case: case.handler.__name__,
    )
    def test_response_schema_refers_to_the_registered_model(
        self, app_serving_handler_of_case: web.Application, case: _ResponseSchemaCase
    ) -> None:
        spec = generate_openapi("Test", [app_serving_handler_of_case])

        response = spec["paths"]["/items"]["get"]["responses"]["200"]
        assert response["content"]["application/json"]["schema"] == case.expected_schema
        assert "_ItemResponseModel" in spec["components"]["schemas"]


@dataclass(frozen=True)
class _SpecCommandCase:
    description: str
    cli: click.Group


class TestGenerateOpenAPISpecCommand:
    @pytest.mark.parametrize(
        "case",
        [
            _SpecCommandCase(description="coordinator", cli=coordinator_cli),
            _SpecCommandCase(description="worker", cli=worker_cli),
        ],
        ids=lambda case: case.description,
    )
    def test_writes_the_spec_to_stdout(self, case: _SpecCommandCase) -> None:
        result = CliRunner().invoke(case.cli, ["generate-openapi-spec"])

        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout)["paths"]

    @pytest.mark.parametrize("list_handler_path", ["/v1/api/slots", "/v1/api/worker"])
    def test_coordinator_spec_describes_list_handlers_as_arrays(
        self, list_handler_path: str
    ) -> None:
        result = CliRunner().invoke(coordinator_cli, ["generate-openapi-spec"])

        assert result.exit_code == 0, result.output
        spec = json.loads(result.stdout)
        response = spec["paths"][list_handler_path]["get"]["responses"]["200"]
        assert response["content"]["application/json"]["schema"]["type"] == "array"
