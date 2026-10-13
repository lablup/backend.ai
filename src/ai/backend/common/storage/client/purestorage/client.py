from __future__ import annotations

import threading

import httpx

from ai.backend.common.storage.client.purestorage.types import (
    PureStorageArray,
    PureStorageClientArgs,
)


class PureStorageClient:
    """Synchronous Purity API client; keeps its session token and logs in again when it expires."""

    _api_token: str
    _api_version: str
    _http: httpx.Client
    _lock: threading.Lock
    _token: str | None

    def __init__(self, args: PureStorageClientArgs) -> None:
        self._api_token = args.api_token
        self._api_version = args.api_version
        self._http = httpx.Client(
            base_url=args.endpoint, verify=args.verify_ssl, timeout=args.timeout
        )
        self._lock = threading.Lock()
        self._token = None

    def close(self) -> None:
        self._http.close()

    def _login(self) -> str:
        resp = self._http.post("/api/login", headers={"api-token": self._api_token})
        resp.raise_for_status()
        return resp.headers["x-auth-token"]

    def _ensure_token(self, *, renew: bool) -> str:
        with self._lock:
            if renew or self._token is None:
                self._token = self._login()
            return self._token

    def _get(self, path: str) -> httpx.Response:
        """Sends a GET with the kept token, logging in again once when it is rejected."""
        resp = self._http.get(path, headers=self._auth_headers(self._ensure_token(renew=False)))
        if resp.status_code == httpx.codes.UNAUTHORIZED:
            resp = self._http.get(path, headers=self._auth_headers(self._ensure_token(renew=True)))
        resp.raise_for_status()
        return resp

    def _auth_headers(self, token: str) -> dict[str, str]:
        return {"x-auth-token": token}

    def get_array(self) -> PureStorageArray:
        array = self._get(f"/api/{self._api_version}/arrays").json()["items"][0]
        return PureStorageArray(
            array_id=array["id"],
            array_name=array["name"],
            os=array["os"],
            version=array["version"],
        )
