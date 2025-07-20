from collections.abc import Mapping
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Final

import aiohttp
import yarl

from ai.backend.manager.errors.storage import (
    VFolderBadRequest,
    VFolderGone,
    VFolderNotFound,
    VFolderOperationFailed,
)

AUTH_TOKEN_HDR: Final = "X-BackendAI-Storage-Auth-Token"


@dataclass
class StorageProxyClientArgs:
    endpoint: yarl.URL
    secret: str


class StorageProxyHTTPClient:
    _session_client: aiohttp.ClientSession
    _endpoint: yarl.URL
    _secret: str

    def __init__(self, session_client: aiohttp.ClientSession, args: StorageProxyClientArgs):
        self._session_client = session_client
        self._endpoint = args.endpoint
        self._secret = args.secret

    async def request(
        self,
        method: str,
        url: str,
        *,
        body: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        """
        Make an HTTP request using the session client.

        :param method: HTTP method (GET, POST, etc.)
        :param url: URL to send the request to
        :param body: JSON body data to send with the request
        :return: Response object from the request
        """
        headers = {
            AUTH_TOKEN_HDR: self._secret,
        }
        async with self._session_client.request(
            method,
            self._endpoint / url,
            headers=headers,
            json=body,
        ) as client_resp:
            if client_resp.status // 100 == 2:
                return await client_resp.json()
            match client_resp.status:
                case HTTPStatus.BAD_REQUEST:
                    raise VFolderBadRequest(
                        extra_msg="Bad request to storage proxy",
                    )
                case HTTPStatus.NOT_FOUND:
                    raise VFolderNotFound(
                        extra_msg="Requested resource not found",
                    )
                case HTTPStatus.GONE:
                    raise VFolderGone(
                        extra_msg=(
                            "The requested resource is gone. It may have been deleted or moved."
                        ),
                    )
                case HTTPStatus.INTERNAL_SERVER_ERROR:
                    raise VFolderOperationFailed(
                        extra_msg="Internal server error from storage proxy",
                    )
                case _:
                    raise VFolderOperationFailed(
                        extra_msg=f"Unexpected error {client_resp.status} from storage proxy",
                    )
