from __future__ import annotations

import threading

import httpx

from ai.backend.common.storage.client.hammerspace.types import (
    HammerspaceClientArgs,
    HammerspaceSite,
)


class HammerspaceClient:
    """Synchronous Hammerspace API client; keeps its session and logs in again when it expires."""

    _username: str
    _password: str
    _http: httpx.Client
    _lock: threading.Lock
    _logged_in: bool

    def __init__(self, args: HammerspaceClientArgs) -> None:
        self._username = args.username
        self._password = args.password
        self._http = httpx.Client(
            base_url=args.address, verify=args.verify_ssl, timeout=args.timeout
        )
        self._lock = threading.Lock()
        self._logged_in = False

    def close(self) -> None:
        self._http.close()

    def _ensure_session(self, *, renew: bool) -> None:
        with self._lock:
            if not renew and self._logged_in:
                return
            self._logged_in = False
            resp = self._http.post(
                "/login",
                data={"username": self._username, "password": self._password},
            )
            resp.raise_for_status()
            self._logged_in = True

    def _get(self, path: str) -> httpx.Response:
        """Sends a GET in the kept session, logging in again once when it is rejected."""
        self._ensure_session(renew=False)
        resp = self._http.get(path)
        if resp.status_code == httpx.codes.UNAUTHORIZED:
            self._ensure_session(renew=True)
            resp = self._http.get(path)
        resp.raise_for_status()
        return resp

    def list_sites(self) -> tuple[HammerspaceSite, ...]:
        sites = self._get("/sites").json()
        return tuple(HammerspaceSite(name=site["name"], type=site["type"]) for site in sites)
