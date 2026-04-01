"""Deployment-specific recorder context for deployment coordinator."""

from __future__ import annotations

from uuid import UUID

from ai.backend.manager.sokovan.recorder.context import RecorderContext

# Deployment-specific type alias
DeploymentRecorderContext = RecorderContext[UUID]

__all__ = [
    "DeploymentRecorderContext",
]
