"""
Keypair DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.keypair.response import (
    IssueMyKeypairPayload,
    RevokeMyKeypairPayload,
    SwitchMyMainAccessKeyPayload,
)

__all__ = (
    "IssueMyKeypairPayload",
    "RevokeMyKeypairPayload",
    "SwitchMyMainAccessKeyPayload",
)
