"""Backward-compatibility redirect.

The deployment handler has been migrated to
``ai.backend.manager.api.rest.deployment.handler``.
"""

from ai.backend.manager.api.rest.deployment.handler import DeploymentAPIHandler

__all__ = ("DeploymentAPIHandler",)
