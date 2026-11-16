"""Applying the kind again changes nothing."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

from ai.backend.manager.seed.types import SeedKind


async def test_applying_again_changes_nothing(
    assert_idempotent: Callable[[SeedKind, Path], Awaitable[None]],
    storage_backend_type_seed_dir: Path,
) -> None:
    await assert_idempotent(SeedKind.STORAGE_BACKEND_TYPE, storage_backend_type_seed_dir)
