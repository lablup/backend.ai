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

    default_version = "0.10.0"
    default_known_versions = [
        "0.10.0|linux_arm64|877c45f5a5f502a4147bbfd809d1305d5afbde8be1d53036fc67d58dc899c03b|8610020",
        "0.10.0|linux_x86_64|89ce91a6b895506ee31665caf0b96bf290a5889c35b82e96e9b4cdc4b164dc98|9921362",
        "0.10.0|macos_arm64|a2f8a62f92f1ac53895196c769ac8d9de83044bbea444d2aa62ddf19dbc074f1|4448491",
        "0.10.0|macos_x86_64|ebfa77f75789b9258e7b7ee1094849e63a47e1abacf0cd4fc3bc233bd6fea7d6|4556920",
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
