"""Writes the SessionWorkload of a session into its compute cluster (suggestion-1122 13.1)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Final, Self

import yaml
from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException
from kubernetes_asyncio.config import kube_config

from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import SessionId
from ai.backend.kube.crd.base import CRD_VERSION
from ai.backend.kube.crd.scheduling import Queue
from ai.backend.kube.crd.session import SessionWorkload
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.clients.compute_cluster.mapping import (
    LABEL_MANAGED_BY,
    LABEL_SESSION_ID,
    MANAGED_BY,
    SessionObjects,
    queue_name,
)
from ai.backend.manager.data.compute_cluster.types import ProjectQueueData

log = StructuredLogger(logging.getLogger(__spec__.name))

ANNOTATION_TERMINATION_REASON: Final = "backend.ai/termination-reason"
_MERGE_PATCH: Final = "application/merge-patch+json"
_JSON_PATCH: Final = "application/json-patch+json"
_SW = SessionWorkload.crd
_Q = Queue.crd


class ComputeClusterClient:
    """One compute cluster's API server, reached with the kubeconfig the cluster was registered with."""

    _api: client.ApiClient
    _core: client.CoreV1Api
    _custom: client.CustomObjectsApi

    def __init__(self, api: client.ApiClient) -> None:
        self._api = api
        self._core = client.CoreV1Api(api)
        self._custom = client.CustomObjectsApi(api)

    @classmethod
    async def from_kubeconfig(cls, kubeconfig: str) -> Self:
        configuration = client.Configuration()
        await kube_config.load_kube_config_from_dict(
            yaml.safe_load(kubeconfig), client_configuration=configuration
        )
        return cls(client.ApiClient(configuration=configuration))

    async def close(self) -> None:
        await self._api.close()

    async def ensure_namespace(self, name: str, labels: dict[str, str]) -> None:
        try:
            await self._core.create_namespace({
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": name, "labels": {LABEL_MANAGED_BY: MANAGED_BY, **labels}},
            })
        except ApiException as e:
            if e.status != 409:
                raise

    async def sync_project_queue(self, resource_group: str, queue: ProjectQueueData) -> str:
        """Make the resource group's queue and the project's queue under it match the Manager.

        Returns the project queue's name, which the session's workload names.
        """
        parent = queue_name(resource_group)
        child = queue_name(resource_group, queue.project_id)
        await self._upsert_queue(parent, {"resources": {}})
        limits = {
            slot: {"limit": value}
            for slot, value in queue.total_resource_slots.items()
            if slot in ("cpu", "mem")
        }
        await self._upsert_queue(child, {"parentQueue": parent, "resources": limits})
        if queue.fair_share_factor is not None:
            await self._custom.patch_cluster_custom_object_status(
                _Q.group,
                CRD_VERSION,
                _Q.plural,
                child,
                {
                    "status": {
                        "fairShareFactor": float(queue.fair_share_factor),
                        "lastSyncedAt": datetime.now(UTC).isoformat(),
                    }
                },
                _content_type=_MERGE_PATCH,
            )
        return child

    async def _upsert_queue(self, name: str, spec: dict[str, Any]) -> None:
        body = {
            "apiVersion": _Q.api_version,
            "kind": _Q.kind,
            "metadata": {"name": name, "labels": {LABEL_MANAGED_BY: MANAGED_BY}},
            "spec": spec,
        }
        try:
            await self._custom.create_cluster_custom_object(_Q.group, CRD_VERSION, _Q.plural, body)
        except ApiException as e:
            if e.status != 409:
                raise
            # Replace the whole spec: a merge patch cannot drop a limit the project no longer has.
            await self._custom.patch_cluster_custom_object(
                _Q.group,
                CRD_VERSION,
                _Q.plural,
                name,
                [{"op": "replace", "path": "/spec", "value": spec}],
                _content_type=_JSON_PATCH,
            )

    async def create_session(self, objects: SessionObjects) -> None:
        """Create the Secrets, then the workload, then hand the Secrets to the workload.

        Every name is derived from the session id, so a retried call finds what exists.
        """
        namespace = objects.workload["metadata"]["namespace"]
        secrets = [objects.secret] + ([objects.pull_secret] if objects.pull_secret else [])
        for secret in secrets:
            await self._create(self._core.create_namespaced_secret(namespace, secret))
        await self._create(
            self._custom.create_namespaced_custom_object(
                _SW.group, CRD_VERSION, namespace, _SW.plural, objects.workload
            )
        )
        created = await self._custom.get_namespaced_custom_object(
            _SW.group, CRD_VERSION, namespace, _SW.plural, objects.workload["metadata"]["name"]
        )
        owner = {
            "apiVersion": _SW.api_version,
            "kind": _SW.kind,
            "name": created["metadata"]["name"],
            "uid": created["metadata"]["uid"],
        }
        for secret in secrets:
            await self._core.patch_namespaced_secret(
                secret["metadata"]["name"],
                namespace,
                {"metadata": {"ownerReferences": [owner]}},
                _content_type=_MERGE_PATCH,
            )

    async def destroy_session(
        self, session_id: SessionId, reason: KernelLifecycleEventReason
    ) -> None:
        """Delete the session's workload; the cluster reports each kernel's end with `reason`."""
        listed = await self._custom.list_cluster_custom_object(
            _SW.group,
            CRD_VERSION,
            _SW.plural,
            label_selector=f"{LABEL_SESSION_ID}={session_id}",
        )
        if not listed["items"]:
            log.debug("session workload already gone", session_id=session_id)
            return
        for item in listed["items"]:
            namespace, name = item["metadata"]["namespace"], item["metadata"]["name"]
            try:
                await self._custom.patch_namespaced_custom_object(
                    _SW.group,
                    CRD_VERSION,
                    namespace,
                    _SW.plural,
                    name,
                    {"metadata": {"annotations": {ANNOTATION_TERMINATION_REASON: str(reason)}}},
                    _content_type=_MERGE_PATCH,
                )
                await self._custom.delete_namespaced_custom_object(
                    _SW.group, CRD_VERSION, namespace, _SW.plural, name
                )
            except ApiException as e:
                if e.status != 404:
                    raise

    async def _create(self, call: Any) -> None:
        try:
            await call
        except ApiException as e:
            if e.status != 409:
                raise
