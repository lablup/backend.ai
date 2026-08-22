from dataclasses import dataclass

from ai.backend.manager.services.deployment.actions.base import DeploymentSingleEntityAction


@dataclass
class DeploymentPolicyBaseAction(DeploymentSingleEntityAction):
    """Base for an operation on a deployment's policy.

    Answered for by the deployment: what is touched lives under it.
    """
