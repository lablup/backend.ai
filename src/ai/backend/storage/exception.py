import json
from typing import Any

from aiohttp import web


class StorageProxyError(Exception):
    pass


class ExecutionError(StorageProxyError):
    pass


class VFolderCreationError(StorageProxyError):
    pass


class VFolderNotFoundError(StorageProxyError):
    pass


class InvalidSubpathError(StorageProxyError):
    pass


class InvalidVolumeError(StorageProxyError):
    pass


class InvalidAPIParameters(web.HTTPBadRequest):
    def __init__(
        self,
        type_suffix: str = "invalid-api-params",
        title: str = "Invalid API parameters",
        msg: str = None,
        data: Any = None,
    ) -> None:
        payload = {
            "type": f"https://api.backend.ai/probs/storage/{type_suffix}",
            "title": title,
        }
        if msg is not None:
            payload["title"] = f"{title} ({msg})"
        if data is not None:
            payload["data"] = data
        super().__init__(
            text=json.dumps(payload),
            content_type="application/problem+json",
        )
