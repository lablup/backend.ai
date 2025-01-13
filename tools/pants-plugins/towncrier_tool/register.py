from __future__ import annotations

from pants.backend.python.subsystems.python_tool_base import PythonToolBase
from pants.backend.python.target_types import ConsoleScript
from pants.core.goals.resolves import ExportableTool
from pants.engine.rules import collect_rules
from pants.engine.unions import UnionRule


class Towncrier(PythonToolBase):
    options_scope = "towncrier"
    name = "Towncrier"
    help = (
        "The utility for auto-generating changelogs from news fragment files "
        "(https://towncrier.readthedocs.io/en/latest/)"
    )

    default_version = "towncrier>=24.8"
    default_main = ConsoleScript("towncrier")
    default_requirements = ["towncrier>=24.8"]

    register_interpreter_constraints = True

    default_lockfile_resource = ("towncrier_tool", "towncrier.lock")


def rules():
    return (
        *collect_rules(),
        UnionRule(ExportableTool, Towncrier),
    )
