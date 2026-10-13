from __future__ import annotations

import httpx

from ai.backend.common.storage.client.gpfs.types import GPFSClientArgs, GPFSCluster


class GPFSClient:
    """Synchronous Spectrum Scale management API client over one kept connection pool."""

    _http: httpx.Client

    def __init__(self, args: GPFSClientArgs) -> None:
        self._http = httpx.Client(
            base_url=args.endpoint,
            auth=(args.username, args.password),
            headers={"Accept": "application/json"},
            verify=args.verify_ssl,
            timeout=args.timeout,
        )

    def close(self) -> None:
        self._http.close()

    def get_cluster(self) -> GPFSCluster:
        resp = self._http.get("/scalemgmt/v2/cluster")
        resp.raise_for_status()
        summary = resp.json()["cluster"]["clusterSummary"]
        return GPFSCluster(
            cluster_name=summary["clusterName"],
            cluster_id=str(summary["clusterId"]),
        )
