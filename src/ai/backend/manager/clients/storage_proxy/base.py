from collections.abc import Mapping
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, AsyncIterator, Final, Optional

import aiohttp
import yarl

from ai.backend.common.json import load_json
from ai.backend.manager.errors.storage import (
    UnexpectedStorageProxyResponseError,
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
    _client_session: aiohttp.ClientSession
    _endpoint: yarl.URL
    _secret: str

    def __init__(self, client_session: aiohttp.ClientSession, args: StorageProxyClientArgs):
        self._client_session = client_session
        self._endpoint = args.endpoint
        self._secret = args.secret

    @actxmgr
    async def request_stream_response(
        self,
        method: str,
        url: str,
        *,
        body: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        """
        Make an HTTP request using the session client.

        :param method: HTTP method (GET, POST, etc.)
        :param url: URL to send the request to
        :param body: JSON body data to send with the request
        :return: Response data as a dictionary, or None if no content
        """
        headers = {
            AUTH_TOKEN_HDR: self._secret,
        }
        async with self._client_session.request(
            method,
            self._endpoint / url,
            headers=headers,
            json=body,
            params=params,
        ) as client_resp:
            if client_resp.status // 100 == 2:
                yield client_resp
                return
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

    async def request(
        self,
        method: str,
        url: str,
        *,
        body: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Optional[Mapping[str, Any]]:
        """
        Make an HTTP request using the session client.

        :param method: HTTP method (GET, POST, etc.)
        :param url: URL to send the request to
        :param body: JSON body data to send with the request
        :return: Response data as a dictionary, or None if no content
        """
        async with self.request_stream_response(
            method, url, body=body, params=params
        ) as response_stream:
            if response_stream.status == HTTPStatus.NO_CONTENT:
                return None
            resp_bytes = await response_stream.read()
            if not resp_bytes:
                return None
            return load_json(resp_bytes)

    async def request_with_response(
        self,
        method: str,
        url: str,
        *,
        body: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        """
        Make an HTTP request and return the response as a dictionary.

        :param method: HTTP method (GET, POST, etc.)
        :param url: URL to send the request to
        :param body: JSON body data to send with the request
        :return: Response object from the request
        """
        response = await self.request(method, url, body=body, params=params)
        if response is None:
            raise UnexpectedStorageProxyResponseError(
                "Unexpected response from storage proxy: None",
            )
        return response
