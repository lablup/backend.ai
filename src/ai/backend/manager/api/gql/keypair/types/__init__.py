"""Keypair GraphQL types package."""

from .filters import KeypairFilterGQL, KeypairOrderByGQL, KeypairOrderFieldGQL
from .inputs import RevokeMyKeypairInputGQL, SwitchMyMainAccessKeyInputGQL, UpdateMyKeypairInputGQL
from .node import KeyPairConnection, KeyPairEdge, KeyPairGQL
from .payloads import (
    IssueMyKeypairPayloadGQL,
    RevokeMyKeypairPayloadGQL,
    SwitchMyMainAccessKeyPayloadGQL,
    UpdateMyKeypairPayloadGQL,
)

__all__ = [
    "KeyPairConnection",
    "KeyPairEdge",
    "KeyPairGQL",
    "KeypairFilterGQL",
    "KeypairOrderByGQL",
    "KeypairOrderFieldGQL",
    "RevokeMyKeypairInputGQL",
    "SwitchMyMainAccessKeyInputGQL",
    "UpdateMyKeypairInputGQL",
    "IssueMyKeypairPayloadGQL",
    "RevokeMyKeypairPayloadGQL",
    "SwitchMyMainAccessKeyPayloadGQL",
    "UpdateMyKeypairPayloadGQL",
]
