"""Keypair GraphQL types package."""

from .filters import KeypairFilterGQL, KeypairOrderByGQL, KeypairOrderFieldGQL
from .inputs import (
    AdminCreateKeypairInputGQL,
    AdminRegisterSSHKeypairInputGQL,
    AdminUpdateKeypairInputGQL,
    RevokeMyKeypairInputGQL,
    SwitchMyMainAccessKeyInputGQL,
    UpdateMyKeypairInputGQL,
)
from .node import KeyPairConnection, KeyPairEdge, KeyPairGQL
from .payloads import (
    AdminCreateKeypairPayloadGQL,
    AdminDeleteKeypairPayloadGQL,
    AdminDeleteSSHKeypairPayloadGQL,
    AdminGetSSHKeypairPayloadGQL,
    AdminRegisterSSHKeypairPayloadGQL,
    AdminUpdateKeypairPayloadGQL,
    CreateKeypairPayloadGQL,
    IssueMyKeypairPayloadGQL,
    RevokeMyKeypairPayloadGQL,
    SSHKeypairNodeGQL,
    SwitchMyMainAccessKeyPayloadGQL,
    UpdateMyKeypairPayloadGQL,
)

__all__ = [
    "AdminCreateKeypairInputGQL",
    "AdminCreateKeypairPayloadGQL",
    "AdminDeleteKeypairPayloadGQL",
    "AdminDeleteSSHKeypairPayloadGQL",
    "AdminGetSSHKeypairPayloadGQL",
    "AdminRegisterSSHKeypairInputGQL",
    "AdminRegisterSSHKeypairPayloadGQL",
    "AdminUpdateKeypairInputGQL",
    "AdminUpdateKeypairPayloadGQL",
    "CreateKeypairPayloadGQL",
    "KeyPairConnection",
    "KeyPairEdge",
    "KeyPairGQL",
    "KeypairFilterGQL",
    "KeypairOrderByGQL",
    "KeypairOrderFieldGQL",
    "RevokeMyKeypairInputGQL",
    "SSHKeypairNodeGQL",
    "SwitchMyMainAccessKeyInputGQL",
    "UpdateMyKeypairInputGQL",
    "IssueMyKeypairPayloadGQL",
    "RevokeMyKeypairPayloadGQL",
    "SwitchMyMainAccessKeyPayloadGQL",
    "UpdateMyKeypairPayloadGQL",
]
