from ..gql_relay import (
    Connection,
)
from .session import ComputeSessionNode


class SessionPendingQueueConnection(Connection):
    class Meta:
        node = ComputeSessionNode
        description = "Added in 25.13.0."
