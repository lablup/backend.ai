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
    AdminKeypairSecretStatusPayloadGQL,
    AdminReencryptKeypairSecretsPayloadGQL,
    AdminRegisterSSHKeypairPayloadGQL,
    AdminUpdateKeypairPayloadGQL,
    CreateKeypairPayloadGQL,
    IssueMyKeypairPayloadGQL,
    KeypairSecretKeyCountGQL,
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
    "AdminKeypairSecretStatusPayloadGQL",
    "AdminRegisterSSHKeypairInputGQL",
    "AdminRegisterSSHKeypairPayloadGQL",
    "AdminReencryptKeypairSecretsPayloadGQL",
    "AdminUpdateKeypairInputGQL",
    "AdminUpdateKeypairPayloadGQL",
    "CreateKeypairPayloadGQL",
    "KeyPairConnection",
    "KeyPairEdge",
    "KeyPairGQL",
    "KeypairFilterGQL",
    "KeypairOrderByGQL",
    "KeypairOrderFieldGQL",
    "KeypairSecretKeyCountGQL",
    "RevokeMyKeypairInputGQL",
    "SSHKeypairNodeGQL",
    "SwitchMyMainAccessKeyInputGQL",
    "UpdateMyKeypairInputGQL",
    "IssueMyKeypairPayloadGQL",
    "RevokeMyKeypairPayloadGQL",
    "SwitchMyMainAccessKeyPayloadGQL",
    "UpdateMyKeypairPayloadGQL",
]
