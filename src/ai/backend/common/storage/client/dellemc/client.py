from __future__ import annotations

import httpx

from ai.backend.common.storage.client.dellemc.types import DellEMCOneFSClientArgs, OneFSCluster


class DellEMCOneFSClient:
    """Synchronous OneFS platform API client over one kept connection pool."""

    _api_version: str
    _http: httpx.Client

    def __init__(self, args: DellEMCOneFSClientArgs) -> None:
        self._api_version = args.api_version
        self._http = httpx.Client(
            base_url=args.endpoint,
            auth=(args.username, args.password),
            verify=args.verify_ssl,
            timeout=args.timeout,
        )

    def close(self) -> None:
        self._http.close()

    def get_cluster(self) -> OneFSCluster:
        resp = self._http.get(f"/platform/{self._api_version}/cluster/config")
        resp.raise_for_status()
        config = resp.json()
        return OneFSCluster(
            cluster_name=config["name"],
            release=config["onefs_version"]["release"],
            build=config["onefs_version"]["build"],
        )
