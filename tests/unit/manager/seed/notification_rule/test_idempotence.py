"""Applying the kind again changes nothing."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

from ai.backend.manager.seed.types import SeedKind


async def test_applying_again_changes_nothing(
    assert_idempotent: Callable[[SeedKind, Path], Awaitable[None]],
    notification_rule_seed_dir: Path,
) -> None:
    await assert_idempotent(SeedKind.NOTIFICATION_RULE, notification_rule_seed_dir)
