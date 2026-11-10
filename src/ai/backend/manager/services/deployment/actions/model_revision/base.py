from dataclasses import dataclass

from ai.backend.manager.services.deployment.actions.base import DeploymentSingleEntityAction


@dataclass
class ModelRevisionBaseAction(DeploymentSingleEntityAction):
    """Base for an operation on a deployment's model revisions.

    Answered for by the deployment: what is touched lives under it.
    """
