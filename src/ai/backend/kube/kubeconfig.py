from __future__ import annotations

import logging

from kubernetes_asyncio import config


async def load_kube_config() -> None:
    """In-cluster credentials when running in a Pod, the local kubeconfig otherwise."""
    try:
        config.load_incluster_config()
    except config.ConfigException:
        await config.load_kube_config()


def quiet_client_logs() -> None:
    """The API client logs every response body at DEBUG; keep it at INFO at any log level."""
    logging.getLogger("kubernetes_asyncio").setLevel(logging.INFO)
