from dataclasses import dataclass

from ai.backend.manager.services.deployment.actions.base import DeploymentSingleEntityAction


@dataclass
class AutoScalingRuleBaseAction(DeploymentSingleEntityAction):
    """Base for an operation on a deployment's auto-scaling rules.

    Answered for by the deployment: what is touched lives under it.
    """
