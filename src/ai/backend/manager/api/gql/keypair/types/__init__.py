"""Keypair GraphQL types package."""

from .inputs import RevokeMyKeypairInputGQL, SwitchMyMainAccessKeyInputGQL
from .payloads import (
    IssueMyKeypairPayloadGQL,
    RevokeMyKeypairPayloadGQL,
    SwitchMyMainAccessKeyPayloadGQL,
)

__all__ = [
    "RevokeMyKeypairInputGQL",
    "SwitchMyMainAccessKeyInputGQL",
    "IssueMyKeypairPayloadGQL",
    "RevokeMyKeypairPayloadGQL",
    "SwitchMyMainAccessKeyPayloadGQL",
]
