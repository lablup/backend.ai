# Copyright 2022 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import annotations

from typing import Iterable

from pants.core.util_rules.external_tool import TemplatedExternalTool
from pants.engine.rules import Rule, collect_rules
from pants.engine.unions import UnionRule
from pants.util.strutil import softwrap


class Science(TemplatedExternalTool):
    options_scope = "science"
    help = softwrap("""A high level tool to build scies with.""")

    default_version = "0.4.1"
    default_known_versions = [
        "0.4.1|linux_arm64|d2983bc3b293ae59f9aad83968a1ac41d1c761b53504819b243fd8a40e5db30f|8547671",
        "0.4.1|linux_x86_64|f5eda054ae3a2ce14e029d723acac7a2e76f21051fdbdad86adfd0916f512887|9706622",
        "0.4.1|macos_arm64|cd2edd426d706181bace3b1663aef429e753072a73b850b69d971136ab23ff92|4286359",
        "0.4.1|macos_x86_64|0b5969f379baa9e32f832996d134ac11b84618103c58a1231d81d5a98c5570e9|4483114",
    ]

    default_url_template = (
        "https://github.com/a-scie/lift/releases/download/v{version}/science-{platform}"
    )

    default_url_platform_mapping = {
        "linux_arm64": "linux-aarch64",
        "linux_x86_64": "linux-x86_64",
        "macos_arm64": "macos-aarch64",
        "macos_x86_64": "macos-x86_64",
    }

    # args = ArgsListOption(example="--release")


def rules() -> Iterable[Rule | UnionRule]:
    return (
        *collect_rules(),
        *Science.rules(),  # type: ignore[call-arg]
    )
