from __future__ import annotations

import threading

import httpx

from ai.backend.common.storage.client.weka.types import WekaClientArgs, WekaCluster


class WekaClient:
    """Synchronous Weka API client; keeps its access token and logs in again when it expires."""

    _username: str
    _password: str
    _organization: str
    _http: httpx.Client
    _lock: threading.Lock
    _token: str | None

    def __init__(self, args: WekaClientArgs) -> None:
        self._username = args.username
        self._password = args.password
        self._organization = args.organization
        self._http = httpx.Client(
            base_url=args.endpoint, verify=args.verify_ssl, timeout=args.timeout
        )
        self._lock = threading.Lock()
        self._token = None

    def close(self) -> None:
        self._http.close()

    def _login(self) -> str:
        resp = self._http.post(
            "/api/v2/login",
            data={
                "username": self._username,
                "password": self._password,
                "org": self._organization,
            },
        )
        resp.raise_for_status()
        access_token: str = resp.json()["data"]["access_token"]
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

    def get_cluster(self) -> WekaCluster:
        cluster = self._get("/api/v2/cluster").json()["data"]
        return WekaCluster(
            cluster_name=cluster["name"],
            status=cluster["status"],
            release=cluster["release"],
        )
