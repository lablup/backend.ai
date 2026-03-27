from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest

column_keys = ["nullable", "index", "unique", "primary_key"]


@pytest.fixture
async def image_aliases(tmpdir: Any) -> AsyncGenerator[Path, None]:
    content = """
aliases:
  - ['my-python',     'test-python:latest', 'x86_64']
  - ['my-python:3.6', 'test-python:3.6-debian', 'aarch64']  # preferred
"""
    p = Path(tmpdir) / "test-image-aliases.yml"
    p.write_text(content)

    yield p
