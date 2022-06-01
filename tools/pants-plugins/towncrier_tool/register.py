from __future__ import annotations

from pants.backend.python.goals import lockfile
from pants.backend.python.goals.lockfile import GeneratePythonLockfile
from pants.backend.python.subsystems.python_tool_base import PythonToolBase
from pants.backend.python.subsystems.setup import PythonSetup
from pants.backend.python.target_types import ConsoleScript
from pants.core.goals.generate_lockfiles import GenerateToolLockfileSentinel
from pants.core.util_rules.config_files import ConfigFilesRequest
from pants.engine.rules import collect_rules, rule
from pants.engine.unions import UnionRule
from pants.option.option_types import (
    ArgsListOption,
    BoolOption,
    FileOption,
    SkipOption,
)
from pants.util.docutil import git_url
from pants.util.strutil import softwrap


class TowncrierSubsystem(PythonToolBase):
    options_scope = "towncrier"
    name = "Towncrier"
    help = (
        "The utility for auto-generating changelogs from news fragment files "
        "(https://towncrier.readthedocs.io/en/latest/)"
    )

    default_version = "towncrier>=21.9"
    default_main = ConsoleScript("towncrier")

    register_interpreter_constraints = True
    default_interpreter_constraints = ["CPython>=3.7,<4"]

    register_lockfile = True
    default_lockfile_resource = ("towncrier_tool", "towncrier.lock")
    default_lockfile_path = "tools/pants-plugins/towncrier_tool/towncrier.lock"
    default_lockfile_url = git_url(default_lockfile_path)

    skip = SkipOption("update-changelog")
    args = ArgsListOption(example="--draft")

    config = FileOption(
        "--config",
        default=None,
        advanced=True,
        help=lambda cls: softwrap(
            f"""
            Path to a towncrier configuration file.

            Setting this option will disable `[{cls.options_scope}].config_discovery`. Use
            this option if the config is located in a non-standard location.
            """,
        ),
    )
    config_discovery = BoolOption(
        "--config-discovery",
        default=True,
        advanced=True,
        help=lambda cls: softwrap(
            f"""
            If true, Pants will include any relevant config files during
            runs (`towncrier.toml`, `pyproject.toml`).

            Use `[{cls.options_scope}].config` instead if your config is in a
            non-standard location.
            """,
        ),
    )

    def config_request(self) -> ConfigFilesRequest:
        # See https://github.com/twisted/towncrier#readme
        # for how Towncrier discovers config files.
        return ConfigFilesRequest(
            specified=self.config,
            specified_option_name=f"[{self.options_scope}].config",
            discovery=self.config_discovery,
            check_existence=["towncrier.toml", "pyproject.toml"],
            check_content={"towncrier.toml": b"[tool.towncrier]", "pyproject.toml": b"[tool.towncrier]"},
        )


class TowncrierLockfileSentinel(GenerateToolLockfileSentinel):
    resolve_name = TowncrierSubsystem.options_scope


@rule
def setup_towncrier_lockfile(
    _: TowncrierLockfileSentinel,
    subsystem: TowncrierSubsystem,
    python_setup: PythonSetup,
) -> GeneratePythonLockfile:
    return GeneratePythonLockfile.from_tool(
        subsystem,
        use_pex=python_setup.generate_lockfiles_with_pex,
    )


def rules():
    return (
        *collect_rules(),
        *lockfile.rules(),
        UnionRule(GenerateToolLockfileSentinel, TowncrierLockfileSentinel),
    )
