from __future__ import annotations

import httpx

from ai.backend.common.storage.client.netapp.types import NetAppClientArgs, NetAppCluster


class NetAppClient:
    """Synchronous ONTAP REST API client over one kept connection pool."""

    _http: httpx.Client

    def __init__(self, args: NetAppClientArgs) -> None:
        self._http = httpx.Client(
            base_url=args.ontap_endpoint,
            auth=(args.ontap_user, args.ontap_password),
            verify=args.verify_ssl,
            timeout=args.timeout,
        )

    def close(self) -> None:
        self._http.close()

    def get_cluster(self) -> NetAppCluster:
        resp = self._http.get("/api/cluster")
        resp.raise_for_status()
        cluster = resp.json()
        return NetAppCluster(
            cluster_name=cluster["name"],
            cluster_uuid=cluster["uuid"],
            version=cluster["version"]["full"],
        )
