from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.compute_cluster import ComputeClusterEntityType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode

__all__ = (
    "ComputeClusterConflict",
    "ComputeClusterNotFound",
    "KubernetesResourceGroupDisabled",
)


class ComputeClusterConflict(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/compute-cluster-conflict"
    error_title = "A compute cluster with the same name already exists."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ComputeClusterEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )


class ComputeClusterNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/compute-cluster-not-found"
    error_title = "The compute cluster is not found."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCALING_GROUP,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class KubernetesResourceGroupDisabled(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/kubernetes-resource-group-disabled"
    error_title = "Kubernetes resource groups are disabled in the manager configuration."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCALING_GROUP,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
