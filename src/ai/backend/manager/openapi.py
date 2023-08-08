import asyncio
import importlib
import inspect
import json
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp_cors
import click
import trafaret as t
from aiohttp.web_urldispatcher import AbstractResource, DynamicResource
from trafaret.lib import _empty

import ai.backend.common.validators as tx
from ai.backend.manager import __version__
from ai.backend.manager.api.session import UndefChecker
from ai.backend.manager.api.utils import Undefined
from ai.backend.manager.models.vfolder import VFolderPermissionValidator
from ai.backend.manager.server import global_subapp_pkgs


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
            return {"oneOf": list(_traverse(s) for s in valid_trafarets)}
        else:
            scheme = valid_trafarets[0]
    if isinstance(scheme, t.Any):
        return {"type": "string"}
    if isinstance(scheme, t.Bool):
        return {"type": "boolean"}
    if isinstance(scheme, t.Dict):
        items = parse_traferet_definition(scheme)
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
            "oneOf": [
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
        and len(
            [
                x
                for x in scheme.trafarets  # type: ignore[attr-defined]
                if (isinstance(x, t.Null) or isinstance(x, UndefChecker))
            ]
        )
        > 0
    )

    return _traverse(scheme), optional


def parse_traferet_definition(root: t.Dict) -> list[dict]:
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
        resp += [{"name": names[0], "schema": schema, "required": not optional}]
    return resp


async def generate_openapi(output_path: Path) -> None:
    cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }

    openapi: dict[str, Any] = {
        "openapi": "3.0.0",
        "info": {
            "title": "Backend.AI Manager API",
            "description": "Backend.AI Manager REST API specification",
            "version": __version__,
        },
        "components": {
            "securitySchemes": {
                "TokenAuth": {"type": "ApiKey", "in": "header", "name": "Authorization: BackendAI"},
            }
        },
        "paths": defaultdict(lambda: {}),
    }
    operation_id_mapping: defaultdict[str, int] = defaultdict(lambda: 0)
    for subapp in global_subapp_pkgs:
        pkg = importlib.import_module("ai.backend.manager.api" + subapp)
        app, _ = pkg.create_app(cors_options)
        prefix = app.get("prefix", "root")
        for route in app.router.routes():
            resource = route.resource
            if not resource:
                continue

            path = "/" + ("" if prefix == "root" else prefix) + resource.canonical
            method = route.method

            if method == "OPTIONS":
                continue

            operation_id = f"{prefix}.{route.handler.__name__}"
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
                    parsed_definition = parse_traferet_definition(request_scheme)
                    if method == "GET" or method == "DELETE":
                        parameters.extend([{**d, "in": "query"} for d in parsed_definition])
                    else:
                        properties = {d["name"]: d["schema"] for d in parsed_definition}
                        required_keys: list[str] = [
                            d["name"] for d in parsed_definition if d["required"]
                        ]
                        route_def["requestBody"] = {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": properties,
                                        "required": required_keys,
                                    }
                                }
                            }
                        }
            route_def["parameters"] = parameters
            route_def["description"] = "\n".join(description)
            openapi["paths"][path][method.lower()] = route_def

    async with aiofiles.open(output_path, mode="w") as fw:
        await fw.write(json.dumps(openapi, ensure_ascii=False, indent=2))


@click.command()
@click.argument("OUTPUT_PATH")
def main(output_path: Path) -> None:
    """
    Generates OpenAPI specification of Backend.AI API.
    """
    asyncio.run(generate_openapi(output_path))


if __name__ == "__main__":
    main()
