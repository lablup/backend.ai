"""Applying the kind again changes nothing."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

import pytest

from ai.backend.manager.seed.types import SeedKind


@pytest.mark.parametrize(
    "kind_name",
    [
        SeedKind.USER_RESOURCE_POLICY,
        SeedKind.PROJECT_RESOURCE_POLICY,
        SeedKind.KEYPAIR_RESOURCE_POLICY,
    ],
)
async def test_applying_again_changes_nothing(
    kind_name: SeedKind,
    assert_idempotent: Callable[[SeedKind, Path], Awaitable[None]],
    resource_policy_seed_dir: Path,
) -> None:
    await assert_idempotent(kind_name, resource_policy_seed_dir)
