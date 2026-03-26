"""
Keypair DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.keypair.request import (
    KeypairFilter,
    KeypairOrderBy,
    RevokeMyKeypairInput,
    SearchMyKeypairsRequest,
    SwitchMyMainAccessKeyInput,
    UpdateMyKeypairInput,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    IssueMyKeypairPayload,
    KeypairNode,
    RevokeMyKeypairPayload,
    SearchMyKeypairsPayload,
    SwitchMyMainAccessKeyPayload,
    UpdateMyKeypairPayload,
)
from ai.backend.common.dto.manager.v2.keypair.types import KeypairOrderField

__all__ = (
    "IssueMyKeypairPayload",
    "KeypairFilter",
    "KeypairNode",
    "KeypairOrderBy",
    "KeypairOrderField",
    "RevokeMyKeypairInput",
    "RevokeMyKeypairPayload",
    "SearchMyKeypairsPayload",
    "SearchMyKeypairsRequest",
    "SwitchMyMainAccessKeyInput",
    "SwitchMyMainAccessKeyPayload",
    "UpdateMyKeypairInput",
    "UpdateMyKeypairPayload",
)
