# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import annotations

from typing import Iterable

from pants.engine.rules import Rule
from pants.engine.unions import UnionRule

from .rules import rules as ruff_rules


def rules() -> Iterable[Rule | UnionRule]:
    return (*ruff_rules(),)
