"""Writes the SessionWorkload of a session into its compute cluster (suggestion-1122 13.1)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final, Self

from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException
from kubernetes_asyncio.config import kube_config

from ai.backend.common.dto.manager.v2.compute_cluster.kubeconfig import (
    InvalidKubeconfigError,
    parse_kubeconfig,
)
from ai.backend.common.dto.manager.v2.resource_group.request import (
    DEFAULT_KUBERNETES_SYSTEM_NAMESPACE,
)
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
from ai.backend.manager.errors.compute_cluster import InvalidKubeconfig

log = StructuredLogger(logging.getLogger(__spec__.name))

ANNOTATION_TERMINATION_REASON: Final = "backend.ai/termination-reason"
_MERGE_PATCH: Final = "application/merge-patch+json"
_JSON_PATCH: Final = "application/json-patch+json"
_SW = SessionWorkload.crd
_Q = Queue.crd


@dataclass(frozen=True)
class NamespacedBinding:
    """A RoleBinding the Manager writes in every session namespace."""

    name: str
    cluster_role: str
    service_account: str


SESSION_NAMESPACE_BINDINGS: Final = (
    NamespacedBinding(
        "backendai-session-controller",
        "backendai-session-controller-namespaced",
        "session-controller",
    ),
    NamespacedBinding(
        "backendai-session-gateway", "backendai-session-gateway-namespaced", "session-gateway"
    ),
    NamespacedBinding("backendai-manager", "backendai-manager-namespaced", "backendai-manager"),
)
"""The cluster components get their namespaced rights only in session namespaces."""


def role_binding_manifest(
    binding: NamespacedBinding, namespace: str, system_namespace: str
) -> dict[str, Any]:
    return {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "RoleBinding",
        "metadata": {
            "name": binding.name,
            "namespace": namespace,
            "labels": {LABEL_MANAGED_BY: MANAGED_BY},
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": binding.cluster_role,
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": binding.service_account,
                "namespace": system_namespace,
            }
        ],
    }


class ComputeClusterClient:
    """One compute cluster's API server, reached with the kubeconfig the cluster was registered with."""

    _api: client.ApiClient
    _core: client.CoreV1Api
    _custom: client.CustomObjectsApi
    _rbac: client.RbacAuthorizationV1Api

    def __init__(self, api: client.ApiClient) -> None:
        self._api = api
        self._core = client.CoreV1Api(api)
        self._custom = client.CustomObjectsApi(api)
        self._rbac = client.RbacAuthorizationV1Api(api)

    @classmethod
    async def from_kubeconfig(cls, kubeconfig: str) -> Self:
        """Load only the validated current context, so a stored kubeconfig never runs a
        command or reads a file on the Manager's host."""
        try:
            parsed = parse_kubeconfig(kubeconfig)
        except InvalidKubeconfigError as e:
            raise InvalidKubeconfig(str(e)) from e
        configuration = client.Configuration()
        await kube_config.load_kube_config_from_dict(
            dict(parsed.config), client_configuration=configuration
        )
        return cls(client.ApiClient(configuration=configuration))

    async def close(self) -> None:
        await self._api.close()

    async def ensure_namespace(
        self,
        name: str,
        labels: dict[str, str],
        *,
        system_namespace: str = DEFAULT_KUBERNETES_SYSTEM_NAMESPACE,
    ) -> None:
        """Create the session namespace and bind the cluster components' namespaced
        ClusterRoles to their ServiceAccounts in `system_namespace`."""
        all_labels = {LABEL_MANAGED_BY: MANAGED_BY, **labels}
        try:
            await self._core.create_namespace({
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": name, "labels": all_labels},
            })
        except ApiException as e:
            if e.status != 409:
                raise
            await self._core.patch_namespace(
                name, {"metadata": {"labels": all_labels}}, _content_type=_MERGE_PATCH
            )
        for binding in SESSION_NAMESPACE_BINDINGS:
            body = role_binding_manifest(binding, name, system_namespace)
            try:
                await self._rbac.create_namespaced_role_binding(name, body)
            except ApiException as e:
                if e.status != 409:
                    raise
                await self._rbac.patch_namespaced_role_binding(
                    binding.name,
                    name,
                    {
                        "metadata": {"labels": body["metadata"]["labels"]},
                        "subjects": body["subjects"],
                    },
                    _content_type=_MERGE_PATCH,
                )

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
