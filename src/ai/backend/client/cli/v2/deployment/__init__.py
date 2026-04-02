from .commands import deployment as deployment
from .policy import policy
from .replica import replica
from .revision import revision

# Register sub-entity groups under the deployment group
deployment.add_command(revision)
deployment.add_command(replica)
deployment.add_command(policy)

__all__ = ("deployment",)
