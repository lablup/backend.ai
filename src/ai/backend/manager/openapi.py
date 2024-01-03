import asyncio
import importlib
import inspect
import json
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import Any, List, get_args, get_type_hints

import aiohttp_cors
import click
import trafaret as t
from aiohttp import web
from aiohttp.web_urldispatcher import AbstractResource, DynamicResource
from pydantic import BaseModel, TypeAdapter
from trafaret.lib import _empty

import ai.backend.common.validators as tx
from ai.backend.manager import __version__
from ai.backend.manager.api.session import UndefChecker
from ai.backend.manager.api.utils import Undefined
from ai.backend.manager.models.vfolder import VFolderPermissionValidator


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


def flatten_or(scheme: t.Trafaret) -> list[t.Trafaret]:
    left, right = scheme.trafarets  # type: ignore[attr-defined]
    items = []
    if isinstance(left, t.Or):
        items.extend(flatten_or(left))
    else:
        items.append(left)

    if isinstance(right, t.Or):
        items.extend(flatten_or(right))
    else:
        items.append(right)
    return items


def _traverse(scheme: t.Trafaret) -> dict:
    if isinstance(scheme, t.Or):
        trafarets = flatten_or(scheme)
        valid_trafarets = [
            x for x in trafarets if not (isinstance(x, t.Null) or isinstance(x, UndefChecker))
        ]
        if len(valid_trafarets) >= 2:
            return {"anyOf": list(_traverse(s) for s in valid_trafarets)}
        else:
            scheme = valid_trafarets[0]
    if isinstance(scheme, t.Any):
        return {"type": "string"}
    if isinstance(scheme, t.Bool):
        return {"type": "boolean"}
    if isinstance(scheme, t.Dict):
        items = parse_trafaret_definition(scheme)
        properties = {d["name"]: d["schema"] for d in items}
        required_keys: list[str] = [d["name"] for d in items if d["required"]]
        return {"type": "object", "properties": properties, "required": required_keys}
    if isinstance(scheme, t.Enum):
        enum_values = scheme.variants  # type: ignore[attr-defined]
        return {"type": "string", "enum": enum_values}
    if isinstance(scheme, t.Float):
        resp = {"type": "integer"}
        if gte := scheme.gte:  # type: ignore[attr-defined]
            resp["minimum"] = gte
        if lte := scheme.lte:  # type: ignore[attr-defined]
            resp["maximum"] = lte
        return resp
    if isinstance(scheme, t.Int):
        resp = {"type": "integer"}
        if gte := scheme.gte:  # type: ignore[attr-defined]
            resp["minimum"] = gte
        if lte := scheme.lte:  # type: ignore[attr-defined]
            resp["maximum"] = lte
        return resp
    if isinstance(scheme, t.List):
        array_items = _traverse(scheme.trafaret)  # type: ignore[attr-defined]
        return {"type": "array", "items": array_items}
    if isinstance(scheme, t.Mapping):
        key_type = scheme.key.__class__.__name__  # type: ignore[attr-defined]
        value_type = scheme.value.__class__.__name__  # type: ignore[attr-defined]
        return {
            "type": "object",
            "description": f"Mapping({key_type} => {value_type})",
            "additionalProperties": True,
        }
    if isinstance(scheme, t.Regexp):
        pattern = scheme.regexp.pattern  # type: ignore[attr-defined]
        return {"type": "string", "pattern": str(pattern)}
    if isinstance(scheme, t.String):
        return {"type": "string"}
    if isinstance(scheme, t.ToBool):
        return {"type": "boolean"}
    if isinstance(scheme, tx.BinarySize):
        return {"type": "string", "description": "Size in binary format (e.g. 2KB, 3M, 4GiB)"}
    if isinstance(scheme, tx.Enum):
        if scheme.use_name:
            values = [e.name for e in scheme.enum_cls]
        else:
            values = [e.value for e in scheme.enum_cls]
        return {"type": "string", "enum": values}
    if isinstance(scheme, tx.JSONString):
        return {"type": "string", "description": "JSON string"}
    if isinstance(scheme, tx.Path):
        return {"type": "string", "description": "POSIX path"}
    if isinstance(scheme, tx.Slug):
        return {"type": "string", "pattern": str(scheme._rx_slug.pattern)}
    if isinstance(scheme, tx.TimeDuration):
        return {
            "anyOf": [
                {
                    "type": "string",
                    "description": (
                        "Human-readable time duration representation (e.g. 2y, 3d, 4m, 5h, 6s, ...)"
                    ),
                },
                {"type": "int", "minimum": 0, "description": "Number of seconds"},
                {"type": "float", "minimum": 0, "description": "Number of seconds"},
            ]
        }
    if isinstance(scheme, tx.URL):
        return {"type": "string", "format": "uri"}
    if isinstance(scheme, tx.UUID):
        return {"type": "string", "format": "uuid"}
    if isinstance(scheme, VFolderPermissionValidator):
        return {"type": "string", "enum": ["ro", "rw", "wd"]}

    if scheme == t.Email:
        return {"type": "string", "format": "email"}
    if scheme == t.IPv4:
        return {"type": "string", "format": "ipv4"}
    if scheme == t.IPv6:
        return {"type": "string", "format": "ipv6"}
    if scheme == t.URL:
        return {"type": "string", "format": "uri"}

    raise ParseError(f"Failed to convert unknown value {scheme} to OpenAPI type")


def parse_trafaret_value(scheme: t.Trafaret) -> tuple[dict, bool]:
    optional = (
        isinstance(scheme, t.Or)
        and len([
            x
            for x in scheme.trafarets  # type: ignore[attr-defined]
            if (isinstance(x, t.Null) or isinstance(x, UndefChecker))
        ])
        > 0
    )

    return _traverse(scheme), optional


def parse_trafaret_definition(root: t.Dict) -> list[dict]:
    resp = []
    for key in root.keys:  # type: ignore[attr-defined]
        names: list[str] = []
        if isinstance(key, tx.AliasedKey):
            names.extend(key.names)
        elif isinstance(key, t.Key):
            names.append(key.name)  # type: ignore[attr-defined]
        schema, optional = parse_trafaret_value(key.trafaret)
        if key.default and key.default != _empty:
            if inspect.isclass(key.default):
                try:
                    default_value = key.default()
                except Exception:
                    default_value = str(key.default)
            elif isinstance(key.default, Undefined):
                default_value = None
            else:
                default_value = key.default

            schema["default"] = default_value
        if hasattr(key, "__openapi_desc__"):
            schema["description"] = getattr(key, "__openapi_desc__")
        resp += [{"name": names[0], "schema": schema, "required": not optional}]
    return resp


def generate_openapi(subapps: list[web.Application], verbose=False) -> dict[str, Any]:
    openapi: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": "Backend.AI Manager API",
            "description": "Backend.AI Manager REST API specification",
            "version": __version__,
            "contact": {
                "name": "Lablup Inc.",
                "url": "https://docs.backend.ai",
                "email": "contect@lablup.com",
            },
        },
        "components": {
            "securitySchemes": {
                "TokenAuth": {
                    "type": "ApiKey",
                    "in": "header",
                    "name": "Authorization: BackendAI",
                    "description": (
                        "Check https://docs.backend.ai/en/latest/manager/common-api/auth.html for"
                        " more information"
                    ),
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
                print(f"parsing {operation_id}")
            operation_id_mapping[operation_id] += 1
            if (operation_id_count := operation_id_mapping[operation_id]) > 1:
                operation_id += f".{operation_id_count}"

            description = []
            if route.handler.__doc__:
                description.append(textwrap.dedent(route.handler.__doc__))

            route_def = {
                "operationId": operation_id,
                "tags": [prefix],
                "responses": {"200": {"description": "Successful response"}},
            }
            parameters = []
            parameters.extend(get_path_parameters(resource))
            if hasattr(route.handler, "_backend_attrs"):
                preconds = []
                handler_attrs = getattr(route.handler, "_backend_attrs")
                if handler_attrs.get("auth_required"):
                    route_def["security"] = [{"TokenAuth": []}]
                if auth_scope := handler_attrs.get("auth_scope"):
                    preconds.append(f"{auth_scope.capitalize()} privilege required.")
                if manager_status := handler_attrs.get("required_server_statuses"):
                    if len(manager_status) > 0:
                        preconds.append(
                            f"Manager status required: {list(manager_status)[0].value.upper()}"
                        )
                    else:
                        preconds.append(
                            "Manager status required: one of "
                            f"{', '.join([e.value.upper() for e in manager_status])}"
                        )
                if preconds:
                    description.append("\n**Preconditions:**")
                    for item in preconds:
                        description.append(f"* {item}")
                    description.append("")
                if request_scheme := handler_attrs.get("request_scheme"):
                    if isinstance(request_scheme, t.Dict):
                        parsed_definition = parse_trafaret_definition(request_scheme)
                        if method == "GET" or method == "DELETE":
                            parameters.extend([{**d, "in": "query"} for d in parsed_definition])
                        else:
                            properties = {d["name"]: d["schema"] for d in parsed_definition}
                            required_keys: list[str] = [
                                d["name"] for d in parsed_definition if d["required"]
                            ]
                            raw_examples = handler_attrs.get("request_examples") or []
                            examples = {
                                f"{operation_id}_Example{i}": {"value": e}
                                for e, i in zip(raw_examples, range(1, len(raw_examples) + 1))
                            }
                            route_def["requestBody"] = {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": properties,
                                            "required": required_keys,
                                        },
                                        "examples": examples,
                                    }
                                }
                            }
                    elif issubclass(request_scheme, BaseModel):
                        schema_name = request_scheme.__name__
                        request_schema = request_scheme.model_json_schema(
                            ref_template="#/components/schemas/{model}"
                        )

                        if additional_definitions := request_schema.pop("$defs", None):
                            openapi["components"]["schemas"].update(additional_definitions)
                        openapi["components"]["schemas"][schema_name] = request_schema
                        route_def["requestBody"] = {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                                }
                            }
                        }
                    else:
                        raise RuntimeError(
                            f"{request_scheme} not considered as a valid request type"
                        )

            route_def["parameters"] = parameters
            route_def["description"] = "\n".join(description)
            type_hints = get_type_hints(route.handler)
            if (
                (ret_type := type_hints.get("return"))
                and (response_cls := getattr(ret_type, "__origin__", ret_type))
                and (issubclass(response_cls, BaseModel) or issubclass(response_cls, list))
            ):
                response_schema: dict[str, Any]
                if issubclass(response_cls, list):
                    arg: type[BaseModel]
                    (arg,) = get_args(ret_type)
                    schema_name = f"{arg.__name__}_List"
                    response_schema = TypeAdapter(List[arg]).json_schema(  # type: ignore[valid-type]
                        ref_template="#/components/schemas/{model}"
                    )
                elif issubclass(response_cls, BaseModel):
                    schema_name = response_cls.__name__
                    response_schema = response_cls.model_json_schema(
                        ref_template="#/components/schemas/{model}"
                    )

                else:
                    raise RuntimeError(f"{arg} not considered as a valid response type")

                if additional_definitions := response_schema.pop("$defs", None):
                    openapi["components"]["schemas"].update(additional_definitions)
                openapi["components"]["schemas"][schema_name] = response_schema
                route_def["responses"] = {
                    "200": {
                        "description": "",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                            }
                        },
                    }
                }
            openapi["paths"][path][method.lower()] = route_def
    return openapi


async def _generate():
    from ai.backend.manager.server import global_subapp_pkgs

    cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }

    subapps: list[web.Application] = []
    for subapp in global_subapp_pkgs:
        pkg = importlib.import_module("ai.backend.manager.api" + subapp)
        app, _ = pkg.create_app(cors_options)
        subapps.append(app)
    return generate_openapi(subapps, verbose=True)


@click.command()
@click.option(
    "--output",
    "-o",
    default="-",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (default: stdout)",
)
def main(output: Path) -> None:
    """
    Generates OpenAPI specification of Backend.AI API.
    """
    openapi = asyncio.run(_generate())
    if output == "-" or output is None:
        print(json.dumps(openapi, ensure_ascii=False, indent=2))
    else:
        with open(output, mode="w") as fw:
            fw.write(json.dumps(openapi, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
