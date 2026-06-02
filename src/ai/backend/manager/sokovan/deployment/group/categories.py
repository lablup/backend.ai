"""Reconcile category/kind enums shared by replica-group reconcile stages."""

from __future__ import annotations

from ai.backend.manager.sokovan.reconciler.base import (
    BaseReconcilerCategory,
    BaseReconcilerKind,
)


class GroupReconcileCategory(BaseReconcilerCategory):
    SCALING = "scaling"
    LIFECYCLE = "lifecycle"


class GroupReconcileKind(BaseReconcilerKind):
    GROUP = "group"
