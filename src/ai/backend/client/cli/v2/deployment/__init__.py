from .access_token import access_token
from .auto_scaling_rule import auto_scaling_rule
from .chat import chat, chat_cache, chat_config, chat_history
from .commands import deployment as deployment
from .options import options
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
deployment.add_command(options)
deployment.add_command(chat)
deployment.add_command(chat_config)
deployment.add_command(chat_cache)
deployment.add_command(chat_history)

__all__ = ("deployment",)
