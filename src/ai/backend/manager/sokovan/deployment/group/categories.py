"""Reconcile kind enum shared by replica-group reconcile stages."""

from __future__ import annotations

from ai.backend.manager.sokovan.reconciler.base import BaseReconcilerKind


class GroupReconcileKind(BaseReconcilerKind):
    GROUP = "group"
