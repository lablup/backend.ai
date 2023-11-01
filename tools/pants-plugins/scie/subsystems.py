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

    default_version = "0.1.1"
    default_known_versions = [
        "0.1.1|linux_arm64|f2082538b6dcd65326cf20ac5aee832f1743f278e36fba9af09fcf81597190ac|5570863",
        "0.1.1|linux_x86_64|edfd24effab7c4ff07c581d278e363aa5e64e9f5e397f13596194ce4583adb3c|6465812",
        "0.1.1|macos_arm64|68a8a09a4792e578da763e621d37695b0e7876dab3b10b54c970722875f05e9a|3455268",
        "0.1.1|macos_x86_64|defcd967c9d51272a749030fcbb57871070cfb7e8943d9391d3a537da69251f0|3573076",
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
