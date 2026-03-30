"""
Keypair DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.keypair.request import (
    AdminCreateKeypairInput,
    AdminDeleteKeypairInput,
    AdminSearchKeypairsInput,
    AdminUpdateKeypairInput,
    KeypairFilter,
    KeypairOrderBy,
    RevokeMyKeypairInput,
    SearchMyKeypairsRequest,
    SwitchMyMainAccessKeyInput,
    UpdateMyKeypairInput,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminCreateKeypairPayload,
    AdminDeleteKeypairPayload,
    AdminSearchKeypairsPayload,
    AdminUpdateKeypairPayload,
    IssueMyKeypairPayload,
    KeypairNode,
    RevokeMyKeypairPayload,
    SearchMyKeypairsPayload,
    SwitchMyMainAccessKeyPayload,
    UpdateMyKeypairPayload,
)
from ai.backend.common.dto.manager.v2.keypair.types import KeypairOrderField

__all__ = (
    "AdminCreateKeypairInput",
    "AdminCreateKeypairPayload",
    "AdminDeleteKeypairInput",
    "AdminDeleteKeypairPayload",
    "AdminSearchKeypairsInput",
    "AdminSearchKeypairsPayload",
    "AdminUpdateKeypairInput",
    "AdminUpdateKeypairPayload",
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
