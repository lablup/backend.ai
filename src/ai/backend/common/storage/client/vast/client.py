from __future__ import annotations

import threading

import httpx

from ai.backend.common.storage.client.vast.types import VASTClientArgs, VASTCluster


class VASTClient:
    """Synchronous VAST API client; keeps its access token and logs in again when it expires."""

    _username: str
    _password: str
    _api_version: str
    _cluster_id: int
    _http: httpx.Client
    _lock: threading.Lock
    _token: str | None

    def __init__(self, args: VASTClientArgs) -> None:
        self._username = args.username
        self._password = args.password
        self._api_version = args.api_version
        self._cluster_id = args.cluster_id
        self._http = httpx.Client(
            base_url=args.endpoint, verify=args.verify_ssl, timeout=args.timeout
        )
        self._lock = threading.Lock()
        self._token = None

    def close(self) -> None:
        self._http.close()

    def _login(self) -> str:
        resp = self._http.post(
            f"/api/{self._api_version}/token/",
            data={"username": self._username, "password": self._password},
        )
        resp.raise_for_status()
        access_token: str = resp.json()["access"]
        return access_token

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
        return {"Authorization": f"Bearer {token}"}

    def get_cluster(self) -> VASTCluster:
        cluster = self._get(f"/api/{self._api_version}/clusters/{self._cluster_id}/").json()
        return VASTCluster(
            cluster_name=cluster["name"],
            state=cluster["state"],
            guid=cluster["guid"],
        )
