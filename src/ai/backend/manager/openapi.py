import asyncio
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast, override

import aiohttp_cors
import click
from aiohttp import web

from ai.backend.common.json import pretty_json_str
from ai.backend.common.openapi import OpenAPIDocumentInfo, OpenAPISpecGenerator
from ai.backend.manager import __version__
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.shutdown import ServerDrainNotifier
from ai.backend.manager.api.rest.tree import build_api_routes
from ai.backend.manager.data.manager_status.types import ManagerStatus

_MANAGER_DOCUMENT_INFO = OpenAPIDocumentInfo(
    title="Backend.AI Manager API",
    description="Backend.AI Manager REST API specification",
    version=__version__,
    security_scheme_name="TokenAuth",
    security_scheme={
        "type": "ApiKey",
        "in": "header",
        "name": "Authorization: BackendAI",
        "description": (
            "Check https://docs.backend.ai/en/latest/manager/common-api/auth.html for"
            " more information"
        ),
    },
)


class ManagerOpenAPISpecGenerator(OpenAPISpecGenerator):
    def __init__(self) -> None:
        super().__init__(_MANAGER_DOCUMENT_INFO)

    @override
    def _describe_preconditions(self, handler_attrs: Mapping[str, Any]) -> list[str]:
        preconds = []
        if auth_scope := handler_attrs.get("auth_scope"):
            preconds.append(f"{auth_scope.capitalize()} privilege required.")
        if manager_status := handler_attrs.get("required_server_statuses"):
            manager_status = cast(frozenset[ManagerStatus], manager_status)
            if len(manager_status) == 1:
                preconds.append(f"Manager status required: {list(manager_status)[0].value.upper()}")
            else:
                preconds.append(
                    "Manager status required: one of "
                    f"{', '.join([e.value.upper() for e in sorted(manager_status)])}"
                )
        return preconds


class _DepStub:
    """No-op stand-in for the runtime deps ``build_api_routes`` injects.

    Handlers only store their deps at construction and route registration reads
    only method signatures, so nothing here is exercised during generation.
    """

    def __getattr__(self, name: str) -> "_DepStub":
        return self

    def __call__(self, *args: Any, **kwargs: Any) -> "_DepStub":
        return self


async def generate() -> dict[str, Any]:
    cors_options = {
        "*": aiohttp_cors.ResourceOptions(  # type: ignore[no-untyped-call]
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }
    stub: Any = _DepStub()
    # reuse build_api_routes() (the single source of truth for routes) with stub deps
    root_registry = RouteRegistry.create("", cors_options)
    for sub in build_api_routes(
        processors=stub,
        adapters=stub,
        cors_options=cors_options,
        config_provider=stub,
        error_monitor=stub,
        gql_context_deps=stub,
        valkey_rate_limit=None,
        root_app=web.Application(),
        stream_cleanup_handler=stub,
        health_probe=stub,
        drain_notifier=ServerDrainNotifier(),
        pidx=0,
    ):
        root_registry.add_subregistry(sub)

    subapps: list[web.Application] = []
    for prefix, app, _reg in root_registry.collect_apps():
        app["_registry_prefix"] = prefix
        subapps.append(app)
    return ManagerOpenAPISpecGenerator().generate(subapps, verbose=True)


@click.command()
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Output file path (default: stdout)",
)
def main(output: Path | None) -> None:
    """
    Generates OpenAPI specification of Backend.AI API.
    """
    openapi = asyncio.run(generate())
    if output is None:
        print(pretty_json_str(openapi))
    else:
        with output.open(mode="w") as fw:
            fw.write(pretty_json_str(openapi))


if __name__ == "__main__":
    main()
