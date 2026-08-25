from dataclasses import dataclass

from ai.backend.manager.services.deployment.actions.base import DeploymentSingleEntityAction


@dataclass
class DeploymentReplicaBaseAction(DeploymentSingleEntityAction):
    """Base for an operation on a deployment's replicas.

    Answered for by the deployment: what is touched lives under it.
    """
