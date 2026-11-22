from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.compute_cluster import ComputeClusterEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass(frozen=True)
class CreateComputeClusterAction(BaseGlobalAction):
    """Register a Kubernetes cluster. ``kubeconfig`` is plaintext; the service encrypts it.

    ``api_server`` is read from the kubeconfig; a given value must match it."""

    name: str
    description: str | None
    api_server: str | None
    kubeconfig: str = field(repr=False)
    namespace_prefix: str
    gateway_addr: str | None
    gateway_public_key: str | None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ComputeClusterEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_create_compute_cluster"
