# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""A Self Contained Interpreted Executable Launcher.

See https://github.com/a-scie/jump for details.
"""

from __future__ import annotations

from typing import Iterable

from pants.engine.rules import Rule
from pants.engine.target import Target
from pants.engine.unions import UnionRule

from .rules import rules as scie_rules
from .target_types import ScieTarget


def rules() -> Iterable[Rule | UnionRule]:
    return (*scie_rules(),)


def target_types() -> Iterable[type[Target]]:
    return (ScieTarget,)
