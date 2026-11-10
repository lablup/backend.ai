from dataclasses import dataclass

from ai.backend.manager.services.deployment.actions.base import DeploymentSingleEntityAction


@dataclass
class DeploymentAccessTokenBaseAction(DeploymentSingleEntityAction):
    """Base for an operation on the access tokens a deployment grants.

    Answered for by the deployment: what is touched lives under it.
    """
