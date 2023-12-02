from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    AsyncContextManager,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    Mapping,
    Tuple,
    TypeVar,
)

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import LooseHeaders
from pydantic import BaseModel, TypeAdapter
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from .context import RootContext


WebRequestHandler: TypeAlias = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
WebMiddleware: TypeAlias = Callable[
    [web.Request, WebRequestHandler],
    Awaitable[web.StreamResponse],
]

CORSOptions: TypeAlias = Mapping[str, aiohttp_cors.ResourceOptions]
AppCreator: TypeAlias = Callable[
    [CORSOptions],
    Tuple[web.Application, Iterable[WebMiddleware]],
]

CleanupContext: TypeAlias = Callable[["RootContext"], AsyncContextManager[None]]
BaseResponseModel = TypeVar("BaseResponseModel", bound=BaseModel)


class TypedJSONResponse(web.Response, Generic[BaseResponseModel]):
    def __init__(
        self,
        response: BaseResponseModel,
        *,
        body: bytes | None = None,
        status: int = 200,
        reason: str | None = None,
        headers: LooseHeaders | None = None,
    ):
        text = response.model_dump_json()
        super().__init__(
            text=text,
            body=body,
            status=status,
            reason=reason,
            headers=headers,
            content_type="application/json",
        )


class TypedJSONListResponse(web.Response, Generic[BaseResponseModel]):
    def __init__(
        self,
        response: list[BaseResponseModel],
        *,
        body: bytes | None = None,
        status: int = 200,
        reason: str | None = None,
        headers: LooseHeaders | None = None,
    ):
        text = TypeAdapter(list[BaseResponseModel]).dump_json(response).decode("utf-8")
        super().__init__(
            text=text,
            body=body,
            status=status,
            reason=reason,
            headers=headers,
            content_type="application/json",
        )
