import inspect
import sys
import textwrap
from collections import defaultdict
from typing import Any, Union, get_args, get_origin, get_type_hints

from aiohttp import web
from aiohttp.web_urldispatcher import AbstractResource, DynamicResource
from pydantic import BaseModel

from ai.backend.appproxy.common.types import PydanticResponse
from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam

from . import __version__


class ParseError(Exception):
    pass


def get_path_parameters(resource: AbstractResource) -> list[dict[str, Any]]:
    params = []
    if isinstance(resource, DynamicResource):
        if groupindex := resource._pattern.groupindex:
            params = [
                {"name": param, "in": "path", "required": True, "schema": {"type": "string"}}
                for param in groupindex.keys()
            ]
    return params


def generate_openapi(
    component: str, subapps: list[web.Application], verbose: bool = False
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
        "paths": defaultdict(dict),
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
                handler_attrs = route.handler._backend_attrs
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

            def _parse_schema(model_cls: type[BaseModel]) -> dict[str, Any]:
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

            # Extract types from @api_handler decorated handlers
            # The wrapper function has __wrapped__ attribute pointing to original handler
            original_handler = getattr(route.handler, "__wrapped__", route.handler)
            try:
                original_type_hints = get_type_hints(original_handler)
            except (NameError, AttributeError):
                original_type_hints = {}

            # Extract request parameters from @api_handler signature
            sig = inspect.signature(original_handler)
            for param in sig.parameters.values():
                param_origin = get_origin(param.annotation)

                # Extract request body from BodyParam[Model]
                if param_origin is BodyParam and "requestBody" not in route_def:
                    if not (body_args := get_args(param.annotation)):
                        continue
                    body_model = body_args[0]
                    if isinstance(body_model, type) and issubclass(body_model, BaseModel):
                        schema_name = body_model.__name__
                        body_schema = body_model.model_json_schema(
                            ref_template="#/components/schemas/{model}"
                        )
                        if additional_definitions := body_schema.pop("$defs", None):
                            openapi["components"]["schemas"].update(additional_definitions)
                        openapi["components"]["schemas"][schema_name] = body_schema
                        route_def["requestBody"] = {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                                }
                            }
                        }

                # Extract query parameters from QueryParam[Model]
                if param_origin is QueryParam:
                    if not (query_args := get_args(param.annotation)):
                        continue
                    query_model = query_args[0]
                    if isinstance(query_model, type) and issubclass(query_model, BaseModel):
                        for field_name, field_info in query_model.model_fields.items():
                            param_schema: dict[str, Any] = {"type": "string"}
                            if field_info.annotation:
                                if field_info.annotation is int:
                                    param_schema = {"type": "integer"}
                                elif field_info.annotation is bool:
                                    param_schema = {"type": "boolean"}
                            parameters.append({
                                "name": field_name,
                                "in": "query",
                                "required": field_info.is_required(),
                                "schema": param_schema,
                            })

            # Extract response type from APIResponse[Model] return type
            if ret_type := original_type_hints.get("return"):
                ret_type_origin = get_origin(ret_type)
                if ret_type_origin is APIResponse:
                    if not (response_args := get_args(ret_type)):
                        pass  # No type parameter, skip
                    elif (response_model := response_args[0]) is not type(
                        None
                    ) and response_model is not Any:
                        if isinstance(response_model, type) and issubclass(
                            response_model, BaseModel
                        ):
                            route_def["responses"] = {"200": _parse_schema(response_model)}

            # Fallback: handle PydanticResponse for legacy handlers
            # Uses wrapper's type hints since PydanticResponse is in wrapper's return type
            if not route_def.get("responses"):
                type_hints = get_type_hints(route.handler)
                if (ret_type := type_hints.get("return")) and (
                    ret_type_origin := get_origin(ret_type)
                ):
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
                            elif isinstance(cls, type) and issubclass(
                                cls, web.HTTPTemporaryRedirect
                            ):
                                responses["301"] = {"description": "Redirection"}
                            elif isinstance(cls, type) and issubclass(
                                cls, web.HTTPPermanentRedirect
                            ):
                                responses["302"] = {"description": "Redirection"}

                        route_def["responses"] = responses
                    elif issubclass(ret_type_origin, PydanticResponse):
                        route_def["responses"] = {"200": _parse_schema(get_args(ret_type)[0])}

            openapi["paths"][path][method.lower()] = route_def
    return openapi
