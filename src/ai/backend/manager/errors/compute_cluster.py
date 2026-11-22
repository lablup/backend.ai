from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.compute_cluster import ComputeClusterEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode

__all__ = (
    "ComputeClusterConflict",
    "ComputeClusterInUse",
    "ComputeClusterKubeconfigInvalid",
    "ComputeClusterLost",
    "ComputeClusterNotFound",
    "InvalidKubeconfig",
    "InvalidResourceGroupDriverOptions",
    "KubernetesResourceGroupDisabled",
    "ResourceGroupDriverChangeConflict",
)


class ComputeClusterConflict(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/compute-cluster-conflict"
    error_title = "A compute cluster with the same name already exists."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ComputeClusterEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )


class ComputeClusterNotFound(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/compute-cluster-not-found"
    error_title = "The compute cluster is not found."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ComputeClusterEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class ComputeClusterInUse(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/compute-cluster-in-use"
    error_title = "A resource group still runs its sessions in the compute cluster."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ComputeClusterEntityType(), ActionOperationType.PURGE, ErrorDetail.CONFLICT
        )


class ComputeClusterLost(EntityError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/compute-cluster-lost"
    error_title = "The compute cluster is LOST; no new sessions are placed in it."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ComputeClusterEntityType(), ActionOperationType.GET, ErrorDetail.UNAVAILABLE
        )


class ComputeClusterKubeconfigInvalid(EntityError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/compute-cluster-kubeconfig-invalid"
    error_title = (
        "The stored kubeconfig of the compute cluster no longer validates;"
        " update the cluster's kubeconfig."
    )

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ComputeClusterEntityType(), ActionOperationType.GET, ErrorDetail.UNAVAILABLE
        )


class InvalidKubeconfig(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-kubeconfig"
    error_title = "The kubeconfig is invalid or uses a credential the manager does not accept."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ComputeClusterEntityType(), ActionOperationType.CREATE, ErrorDetail.INVALID_PARAMETERS
        )


class KubernetesResourceGroupDisabled(EntityError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/kubernetes-resource-group-disabled"
    error_title = "Kubernetes resource groups are disabled in the manager configuration."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ResourceGroupEntityType(), ActionOperationType.GET, ErrorDetail.UNAVAILABLE
        )


class InvalidResourceGroupDriverOptions(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-resource-group-driver-options"
    error_title = "The resource group's driver options do not fit its driver."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ResourceGroupEntityType(), ActionOperationType.UPDATE, ErrorDetail.INVALID_PARAMETERS
        )


class ResourceGroupDriverChangeConflict(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/resource-group-driver-change-conflict"
    error_title = "The driver or compute cluster of a resource group cannot change while it has live sessions."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ResourceGroupEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT
        )
