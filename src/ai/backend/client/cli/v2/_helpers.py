"""Shared helpers for v2 CLI commands."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ai.backend.client.cli.types import CLIContext
    from ai.backend.client.v2.v2_registry import V2ClientRegistry


async def create_v2_registry(ctx: CLIContext) -> V2ClientRegistry:
    """Build a ``V2ClientRegistry`` from the current CLI context."""
    from ai.backend.client.v2.auth import HMACAuth
    from ai.backend.client.v2.config import ClientConfig
    from ai.backend.client.v2.v2_registry import V2ClientRegistry

    v2_config = ClientConfig.from_v1_config(ctx.api_config)
    auth = HMACAuth(ctx.api_config.access_key, ctx.api_config.secret_key)
    return await V2ClientRegistry.create(v2_config, auth)


def print_result(data: Any) -> None:
    """Print a Pydantic model or dict as formatted JSON."""
    if hasattr(data, "model_dump"):
        dumped = data.model_dump(mode="json")
    else:
        dumped = data
    json_str = json.dumps(dumped, indent=2, ensure_ascii=False, default=str)
    sys.stdout.write(json_str + "\n")
