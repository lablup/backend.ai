import types
from collections.abc import Mapping
from typing import Any, Union, get_args, get_origin, override

from ai.backend.appproxy.common.types import PydanticResponse
from ai.backend.common.openapi import OpenAPIDocumentInfo, OpenAPISpecGenerator

from . import __version__


class AppProxyOpenAPISpecGenerator(OpenAPISpecGenerator):
    def __init__(self, component: str) -> None:
        super().__init__(
            OpenAPIDocumentInfo(
                title=f"Backend.AI {component} API",
                description=f"Backend.AI {component} REST API specification",
                version=__version__,
                security_scheme_name="X-BackendAI-Token",
                security_scheme={"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
            )
        )

    @override
    def _describe_preconditions(self, handler_attrs: Mapping[str, Any]) -> list[str]:
        if auth_scope := handler_attrs.get("auth_scope"):
            return [
                f"Requires {auth_scope.capitalize()} token present at `X-BackendAI-Token` request header to work."
            ]
        return []

    @override
    def _response_model_type(self, return_annotation: Any) -> Any:
        if get_origin(return_annotation) in (Union, types.UnionType):
            pydantic_responses = [
                member
                for member in get_args(return_annotation)
                if get_origin(member) is PydanticResponse
            ]
            if len(pydantic_responses) > 1:
                raise RuntimeError(
                    "Cannot specify multiple response types for a single API handler"
                )
            return_annotation = pydantic_responses[0] if pydantic_responses else None
        if get_origin(return_annotation) is PydanticResponse:
            return get_args(return_annotation)[0]
        return None
