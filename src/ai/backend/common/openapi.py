import inspect
import logging
import sys
import textwrap
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, get_args, get_origin, get_type_hints

import trafaret as t
from aiohttp import web
from aiohttp.web_urldispatcher import AbstractResource, DynamicResource
from pydantic import BaseModel, TypeAdapter
from pydantic.errors import PydanticInvalidForJsonSchema
from trafaret.lib import _empty

import ai.backend.common.validators as tx
from ai.backend.common.api_handlers import BodyParam, PathParam, QueryParam
from ai.backend.common.types import BackendAISchema
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_SCHEMA_REF_TEMPLATE = "#/components/schemas/{model}"


class OpenAPIParseError(Exception):
    pass


@dataclass(frozen=True)
class OpenAPIDocumentInfo:
    title: str
    description: str
    version: str
    security_scheme_name: str
    security_scheme: Mapping[str, Any]


class OpenAPISpecGenerator(ABC):
    """Builds an OpenAPI document from the routes of aiohttp sub-apps.

    A component supplies the document info and the parts that depend on its handler
    conventions: the precondition lines and the response model of a return annotation.
    """

    _document_info: OpenAPIDocumentInfo

    def __init__(self, document_info: OpenAPIDocumentInfo) -> None:
        self._document_info = document_info

    @abstractmethod
    def _describe_preconditions(self, handler_attrs: Mapping[str, Any]) -> list[str]:
        raise NotImplementedError

    def _response_model_type(self, return_annotation: Any) -> Any:
        """Return a model class or `list[Model]`, or anything else to leave the response undescribed."""
        return return_annotation

    def generate(self, subapps: list[web.Application], verbose: bool = False) -> dict[str, Any]:
        openapi: dict[str, Any] = {
            "openapi": "3.1.0",
            "info": {
                "title": self._document_info.title,
                "description": self._document_info.description,
                "version": self._document_info.version,
                "contact": {
                    "name": "Lablup Inc.",
                    "url": "https://docs.backend.ai",
                    "email": "contect@lablup.com",
                },
            },
            "components": {
                "securitySchemes": {
                    self._document_info.security_scheme_name: dict(
                        self._document_info.security_scheme
                    ),
                },
                "schemas": {},
            },
            "paths": defaultdict(dict),
        }
        operation_id_mapping: defaultdict[str, int] = defaultdict(lambda: 0)
        for app in subapps:
            prefix = app.get("_registry_prefix", app.get("prefix", "root"))
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

                route_def = self._build_operation(openapi, route, resource, prefix, operation_id)
                openapi["paths"][path][method.lower()] = route_def
        return openapi

    def _build_operation(
        self,
        openapi: dict[str, Any],
        route: web.AbstractRoute,
        resource: AbstractResource,
        prefix: str,
        operation_id: str,
    ) -> dict[str, Any]:
        method = route.method
        description = []
        if route.handler.__doc__:
            description.append(textwrap.dedent(route.handler.__doc__))

        route_def: dict[str, Any] = {
            "operationId": operation_id,
            "tags": [prefix],
            "responses": {"200": {"description": "Successful response"}},
        }
        parameters = []
        parameters.extend(self._path_parameters(resource))
        if hasattr(route.handler, "_backend_attrs"):
            handler_attrs = route.handler._backend_attrs
            if handler_attrs.get("auth_required"):
                route_def["security"] = [{self._document_info.security_scheme_name: []}]
            if handler_attrs.get("deprecated"):
                route_def["deprecated"] = True
            if preconds := self._describe_preconditions(handler_attrs):
                description.append("\n**Preconditions:**")
                for item in preconds:
                    description.append(f"* {item}")
                description.append("")
            if request_scheme := handler_attrs.get("request_scheme"):
                if isinstance(request_scheme, t.Dict):
                    parsed_definition = self._parse_trafaret_definition(request_scheme)
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
                            for e, i in zip(
                                raw_examples, range(1, len(raw_examples) + 1), strict=True
                            )
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
                    try:
                        route_def["requestBody"] = self._json_content(
                            self._register_model_schema(openapi, request_scheme)
                        )
                    except PydanticInvalidForJsonSchema as exc:
                        # field type pydantic can't render as JSON schema; document
                        # the operation without its request-body schema
                        log.warning(
                            "openapi: skipping the request-body schema",
                            operation_id=operation_id,
                            exc_info=exc,
                        )
                else:
                    raise RuntimeError(f"{request_scheme} not considered as a valid request type")

        if "requestBody" not in route_def:
            body_model, query_model, path_model = self._api_handler_param_models(route.handler)
            try:
                if body_model is not None:
                    route_def["requestBody"] = self._json_content(
                        self._register_model_schema(openapi, body_model)
                    )

                if query_model is not None:
                    query_schema = query_model.model_json_schema(ref_template=_SCHEMA_REF_TEMPLATE)
                    properties = query_schema.get("properties", {})
                    required_keys = query_schema.get("required", [])
                    for prop_name, prop_schema in properties.items():
                        parameters.append({
                            "name": prop_name,
                            "in": "query",
                            "required": prop_name in required_keys,
                            "schema": prop_schema,
                        })

                if path_model is not None:
                    path_schema = path_model.model_json_schema(ref_template=_SCHEMA_REF_TEMPLATE)
                    properties = path_schema.get("properties", {})
                    for prop_name, prop_schema in properties.items():
                        if not any(p["name"] == prop_name for p in parameters):
                            parameters.append({
                                "name": prop_name,
                                "in": "path",
                                "required": True,
                                "schema": prop_schema,
                            })
            except PydanticInvalidForJsonSchema as exc:
                # param field type pydantic can't render as JSON schema; document
                # the operation without those param/body schemas
                log.warning(
                    "openapi: skipping the request and param schemas",
                    operation_id=operation_id,
                    exc_info=exc,
                )

        route_def["parameters"] = parameters
        route_def["description"] = "\n".join(description)

        try:
            type_hints = get_type_hints(route.handler)
        except (NameError, AttributeError):
            # handlers with unresolvable forward references (e.g. GraphQLView subclasses)
            type_hints = {}
        if (return_annotation := type_hints.get("return")) is not None:
            response_type = self._response_model_type(return_annotation)
            try:
                if (
                    response_schema_ref := self._register_response_schema(openapi, response_type)
                ) is not None:
                    route_def["responses"] = {
                        "200": {"description": "", **self._json_content(response_schema_ref)}
                    }
            except PydanticInvalidForJsonSchema as exc:
                # unrenderable response model; document the operation without
                # its response schema
                log.warning(
                    "openapi: skipping the response schema",
                    operation_id=operation_id,
                    exc_info=exc,
                )
        return route_def

    def _register_response_schema(
        self, openapi: dict[str, Any], response_type: Any
    ) -> dict[str, Any] | None:
        response_cls = getattr(response_type, "__origin__", response_type)
        if not isinstance(response_cls, type):
            return None
        if issubclass(response_cls, list):
            (item_model,) = get_args(response_type)
            schema_name = f"{item_model.__name__}_List"
            response_schema = TypeAdapter(list[item_model]).json_schema(  # type: ignore[valid-type]
                ref_template=_SCHEMA_REF_TEMPLATE
            )
            if additional_definitions := response_schema.pop("$defs", None):
                openapi["components"]["schemas"].update(additional_definitions)
            openapi["components"]["schemas"][schema_name] = response_schema
            return {"$ref": f"#/components/schemas/{schema_name}"}
        if issubclass(response_cls, BaseModel):
            return self._register_model_schema(openapi, response_cls)
        return None

    def _register_model_schema(
        self, openapi: dict[str, Any], model: type[BaseModel]
    ) -> dict[str, Any]:
        schema_name = model.__name__
        model_schema = model.model_json_schema(ref_template=_SCHEMA_REF_TEMPLATE)
        if additional_definitions := model_schema.pop("$defs", None):
            openapi["components"]["schemas"].update(additional_definitions)
        openapi["components"]["schemas"][schema_name] = model_schema
        return {"$ref": f"#/components/schemas/{schema_name}"}

    def _json_content(self, schema: dict[str, Any]) -> dict[str, Any]:
        return {"content": {"application/json": {"schema": schema}}}

    def _path_parameters(self, resource: AbstractResource) -> list[dict[str, Any]]:
        params = []
        if isinstance(resource, DynamicResource):
            if groupindex := resource._pattern.groupindex:
                params = [
                    {"name": param, "in": "path", "required": True, "schema": {"type": "string"}}
                    for param in groupindex.keys()
                ]
        return params

    def _api_handler_param_models(
        self,
        handler: Any,
    ) -> tuple[
        type[BackendAISchema] | None, type[BackendAISchema] | None, type[BackendAISchema] | None
    ]:
        """Return the `BodyParam`, `QueryParam` and `PathParam` models of an `@api_handler`.

        `get_type_hints()` resolves the string annotations that `from __future__ import annotations` leaves.
        """
        body_model: type[BackendAISchema] | None = None
        query_model: type[BackendAISchema] | None = None
        path_model: type[BackendAISchema] | None = None

        try:
            type_hints = get_type_hints(handler)
        except (ValueError, TypeError, NameError):
            return None, None, None

        for param_name, annotation in type_hints.items():
            if param_name == "return":
                continue

            origin = get_origin(annotation)
            if origin is None:
                continue

            args = get_args(annotation)
            if not args:
                continue

            model = args[0]
            if not (isinstance(model, type) and issubclass(model, BackendAISchema)):
                continue

            if origin is BodyParam:
                body_model = model
            elif origin is QueryParam:
                query_model = model
            elif origin is PathParam:
                path_model = model

        return body_model, query_model, path_model

    def _flatten_or(self, scheme: t.Trafaret) -> list[t.Trafaret]:
        left, right = scheme.trafarets  # type: ignore[attr-defined]
        items = []
        if isinstance(left, t.Or):
            items.extend(self._flatten_or(left))
        else:
            items.append(left)

        if isinstance(right, t.Or):
            items.extend(self._flatten_or(right))
        else:
            items.append(right)
        return items

    def _trafaret_schema(self, scheme: t.Trafaret) -> dict[str, Any]:
        if isinstance(scheme, t.Or):
            trafarets = self._flatten_or(scheme)
            valid_trafarets = [x for x in trafarets if not isinstance(x, t.Null)]
            if len(valid_trafarets) >= 2:
                return {"anyOf": [self._trafaret_schema(s) for s in valid_trafarets]}
            scheme = valid_trafarets[0]
        if isinstance(scheme, t.Any):
            return {"type": "string"}
        if isinstance(scheme, t.Bool):
            return {"type": "boolean"}
        if isinstance(scheme, t.Dict):
            items = self._parse_trafaret_definition(scheme)
            properties = {d["name"]: d["schema"] for d in items}
            required_keys: list[str] = [d["name"] for d in items if d["required"]]
            return {"type": "object", "properties": properties, "required": required_keys}
        if isinstance(scheme, t.Enum):
            enum_values = scheme.variants  # type: ignore[attr-defined]
            return {"type": "string", "enum": enum_values}
        if isinstance(scheme, tx.DelimiterSeperatedList):
            return {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of items separated by a delimiter (default: comma). "
                    "Items may contain spaces, but not the delimiter."
                ),
            }
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
            array_items = self._trafaret_schema(scheme.trafaret)  # type: ignore[attr-defined]
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
            return {
                "type": "string",
                "description": (
                    "String composed of alpha-numeric characters with hyphen and underscores in the middle "
                    "(space and dot may be additionally allowed depending on the used locations)"
                ),
            }
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

        if scheme == t.Email:
            return {"type": "string", "format": "email"}
        if scheme == t.IPv4:
            return {"type": "string", "format": "ipv4"}
        if scheme == t.IPv6:
            return {"type": "string", "format": "ipv6"}
        if scheme == t.URL:
            return {"type": "string", "format": "uri"}

        raise OpenAPIParseError(f"Failed to convert unknown value {scheme} to OpenAPI type")

    def _parse_trafaret_definition(self, root: t.Dict) -> list[dict[str, Any]]:
        resp = []
        for key in root.keys:  # type: ignore[attr-defined]
            names: list[str] = []
            if isinstance(key, tx.AliasedKey):
                names.extend(key.names)
            elif isinstance(key, t.Key):
                names.append(key.name)  # type: ignore[attr-defined]
            schema = self._trafaret_schema(key.trafaret)
            optional = isinstance(key.trafaret, t.Or) and any(
                isinstance(x, t.Null)
                for x in key.trafaret.trafarets  # type: ignore[attr-defined]
            )
            if key.default and key.default != _empty:
                if inspect.isclass(key.default):
                    try:
                        default_value = key.default()
                    except Exception:
                        default_value = str(key.default)
                else:
                    default_value = key.default

                schema["default"] = default_value
            if hasattr(key, "__openapi_desc__"):
                schema["description"] = key.__openapi_desc__
            resp += [{"name": names[0], "schema": schema, "required": not optional}]
        return resp
