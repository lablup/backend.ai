from .access_token import access_token
from .auto_scaling_rule import auto_scaling_rule
from .commands import deployment as deployment
from .policy import policy
from .replica import replica
from .revision import revision
from .revision_preset import revision_preset

# Register sub-entity groups under the deployment group
deployment.add_command(revision)
deployment.add_command(replica)
deployment.add_command(policy)
deployment.add_command(revision_preset)
deployment.add_command(access_token)
deployment.add_command(auto_scaling_rule)

__all__ = ("deployment",)
