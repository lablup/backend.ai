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

    default_version = "0.3.0"
    default_known_versions = [
        "0.3.0|linux_arm64|8a134f2f307137319300d695aa177551a4a4d508cd6324a0aad09d7365edfdef|6364946",
        "0.3.0|linux_x86_64|60730e7d03888254d7b41f5aace431f4264ee20d80924b989d4106b3e2f238dc|7258131",
        "0.3.0|macos_arm64|badfafe685138bf8606d96e7501723f24b9127b9d4e415e2125cf4f06f7f7f64|4185377",
        "0.3.0|macos_x86_64|bcae03dbd58b8412f1b3e62f1d882b424a15e60848c392dd4c19601cd234477c|4317644",
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
