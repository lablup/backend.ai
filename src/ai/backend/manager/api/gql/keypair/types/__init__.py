"""Keypair GraphQL types package."""

from .filters import KeypairFilterGQL, KeypairOrderByGQL, KeypairOrderFieldGQL
from .inputs import (
    AdminCreateKeypairInputGQL,
    AdminUpdateKeypairInputGQL,
    RevokeMyKeypairInputGQL,
    SwitchMyMainAccessKeyInputGQL,
    UpdateMyKeypairInputGQL,
)
from .node import KeyPairConnection, KeyPairEdge, KeyPairGQL
from .payloads import (
    AdminCreateKeypairPayloadGQL,
    AdminDeleteKeypairPayloadGQL,
    AdminUpdateKeypairPayloadGQL,
    IssueMyKeypairPayloadGQL,
    RevokeMyKeypairPayloadGQL,
    SwitchMyMainAccessKeyPayloadGQL,
    UpdateMyKeypairPayloadGQL,
)

__all__ = [
    "AdminCreateKeypairInputGQL",
    "AdminCreateKeypairPayloadGQL",
    "AdminDeleteKeypairPayloadGQL",
    "AdminUpdateKeypairInputGQL",
    "AdminUpdateKeypairPayloadGQL",
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
