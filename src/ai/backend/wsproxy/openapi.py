import sys
import textwrap
from collections import defaultdict
from typing import Any, Union, get_args, get_origin, get_type_hints

from aiohttp import web
from aiohttp.web_urldispatcher import AbstractResource, DynamicResource
from pydantic import BaseModel

from . import __version__
from .types import PydanticResponse


class ParseError(Exception):
    pass


def get_path_parameters(resource: AbstractResource) -> list[dict]:
    params = []
    if isinstance(resource, DynamicResource):
        if groupindex := resource._pattern.groupindex:
            params = [
                {"name": param, "in": "path", "required": True, "schema": {"type": "string"}}
                for param in groupindex.keys()
            ]
    return params


def generate_openapi(
    component: str, subapps: list[web.Application], verbose=False
) -> dict[str, Any]:
    openapi: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": f"Backend.AI {component} API",
            "description": f"Backend.AI {component} REST API specification",
            "version": __version__,
            "contact": {
                "name": "Lablup Inc.",
                "url": "https://docs.backend.ai",
                "email": "contect@lablup.com",
            },
        },
        "components": {
            "securitySchemes": {
                "X-BackendAI-Token": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                },
            },
            "schemas": {},
        },
        "paths": defaultdict(lambda: {}),
    }
    operation_id_mapping: defaultdict[str, int] = defaultdict(lambda: 0)
    for app in subapps:
        prefix = app.get("prefix", "root")
        for route in app.router.routes():
            resource = route.resource
            if not resource:
                continue

            if "_root_app" not in app:
                path = "/" + ("" if prefix == "root" else prefix) + resource.canonical
            else:
                path = resource.canonical
            method = route.method

            if method == "OPTIONS":
                continue

            operation_id = f"{prefix}.{route.handler.__name__}"
            if verbose:
                sys.stderr.write(f"parsing {operation_id}\n")
                sys.stderr.flush()
            operation_id_mapping[operation_id] += 1
            if (operation_id_count := operation_id_mapping[operation_id]) > 1:
                operation_id += f".{operation_id_count}"

            description = []
            if route.handler.__doc__:
                description.append(textwrap.dedent(route.handler.__doc__))

            route_def = {
                "operationId": operation_id,
                "tags": [prefix],
                "responses": dict(),
            }
            parameters = []
            parameters.extend(get_path_parameters(resource))
            if hasattr(route.handler, "_backend_attrs"):
                preconds = []
                handler_attrs = getattr(route.handler, "_backend_attrs")
                if handler_attrs.get("auth_required"):
                    route_def["security"] = [{"X-BackendAI-Token": []}]
                if auth_scope := handler_attrs.get("auth_scope"):
                    preconds.append(
                        f"Requires {auth_scope.capitalize()} token present at `X-BackendAI-Token` request header to work."
                    )
                if preconds:
                    description.append("\n**Preconditions:**")
                    for item in preconds:
                        description.append(f"* {item}")
                    description.append("")
                if request_scheme := handler_attrs.get("request_scheme"):
                    if issubclass(request_scheme, BaseModel):
                        schema_name = request_scheme.__name__
                        request_schema = request_scheme.model_json_schema(
                            ref_template="#/components/schemas/{model}"
                        )

                        if additional_definitions := request_schema.pop("$defs", None):
                            openapi["components"]["schemas"].update(additional_definitions)
                        openapi["components"]["schemas"][schema_name] = request_schema
                        route_def["requestBody"] = {
                            "deprecated": handler_attrs.get("deprecated", False),
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                                }
                            },
                        }
                    else:
                        raise RuntimeError(
                            f"{request_scheme} not considered as a valid request type"
                        )

            route_def["parameters"] = parameters
            route_def["description"] = "\n".join(description)
            type_hints = get_type_hints(route.handler)

            def _parse_schema(model_cls: type[BaseModel]) -> dict:
                if not issubclass(model_cls, BaseModel):
                    raise RuntimeError(f"{model_cls} not considered as a valid response type")

                schema_name = model_cls.__name__
                response_schema = model_cls.model_json_schema(
                    ref_template="#/components/schemas/{model}"
                )

                if additional_definitions := response_schema.pop("$defs", None):
                    openapi["components"]["schemas"].update(additional_definitions)
                openapi["components"]["schemas"][schema_name] = response_schema
                return {
                    "description": "",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                        }
                    },
                }

            if (ret_type := type_hints.get("return")) and (ret_type_origin := get_origin(ret_type)):
                if ret_type_origin == Union:
                    response_classes = get_args(ret_type)
                    responses = dict()

                    for cls in response_classes:
                        if (subclass_origin := get_origin(cls)) and issubclass(
                            subclass_origin, PydanticResponse
                        ):
                            if "200" in responses:
                                raise RuntimeError(
                                    "Cannot specify multiple response types for a single API handler"
                                )
                            responses["200"] = _parse_schema(get_args(cls)[0])
                        elif issubclass(cls, web.HTTPTemporaryRedirect):
                            responses["301"] = {"Description": "Redirection"}
                        elif issubclass(cls, web.HTTPPermanentRedirect):
                            responses["302"] = {"Description": "Redirection"}

                    route_def["responses"] = responses
                elif issubclass(ret_type_origin, PydanticResponse):
                    route_def["responses"] = {"200": _parse_schema(get_args(ret_type)[0])}

            openapi["paths"][path][method.lower()] = route_def
    return openapi
