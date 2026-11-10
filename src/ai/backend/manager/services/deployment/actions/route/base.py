from dataclasses import dataclass

from ai.backend.manager.services.deployment.actions.base import DeploymentSingleEntityAction


@dataclass
class RouteBaseAction(DeploymentSingleEntityAction):
    """Base for an operation on a deployment's routes.

    Answered for by the deployment: what is touched lives under it.
    """
