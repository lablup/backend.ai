"""Deployment-specific recorder for deployment coordinator."""

from __future__ import annotations

from uuid import UUID

from ai.backend.manager.sokovan.recorder.recorder import TransitionRecorder

# Deployment-specific type alias
DeploymentTransitionRecorder = TransitionRecorder[UUID]

__all__ = [
    "DeploymentTransitionRecorder",
]
