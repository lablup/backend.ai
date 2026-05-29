from __future__ import annotations

from dataclasses import dataclass

from pants.backend.python.target_types import PythonSourceField
from pants.core.goals.lint import LintResult, LintTargetsRequest, Partitions
from pants.core.util_rules.partitions import Partition
from pants.engine.env_vars import EnvironmentVars, EnvironmentVarsRequest
from pants.engine.fs import Digest, MergeDigests, PathGlobs, Snapshot
from pants.engine.process import FallibleProcessResult, Process
from pants.engine.rules import Get, collect_rules, concurrently, rule
from pants.engine.target import FieldSet
from pants.option.option_types import SkipOption
from pants.option.subsystem import Subsystem
from pants.util.logging import LogLevel


class VisibilityCheckerSubsystem(Subsystem):
    options_scope = "visibility-checker"
    name = "visibility-checker"
    help = "Check src/ai/backend import visibility chains against BUILD visibility rules."

    skip = SkipOption("lint")


@dataclass(frozen=True)
class VisibilityCheckerFieldSet(FieldSet):
    required_fields = (PythonSourceField,)
    source: PythonSourceField


class VisibilityCheckerRequest(LintTargetsRequest):
    field_set_type = VisibilityCheckerFieldSet
    tool_subsystem = VisibilityCheckerSubsystem


@rule(level=LogLevel.DEBUG)
async def partition_visibility_checker(
    request: VisibilityCheckerRequest.PartitionRequest[VisibilityCheckerFieldSet],
    visibility_checker: VisibilityCheckerSubsystem,
) -> Partitions[VisibilityCheckerFieldSet, None]:
    if visibility_checker.skip or not request.field_sets:
        return Partitions()

    backend_field_sets = tuple(
        field_set
        for field_set in request.field_sets
        if field_set.source.file_path.startswith("src/ai/backend/")
    )
    if not backend_field_sets:
        return Partitions()

    # The checker evaluates the whole src/ai/backend graph in one pass, so a single
    # representative element is enough to make `pants lint` invoke it once.
    return Partitions((Partition((backend_field_sets[0],), None),))


@rule(desc="Check Backend.AI visibility rules", level=LogLevel.DEBUG)
async def run_visibility_checker(
    request: VisibilityCheckerRequest.Batch[VisibilityCheckerFieldSet, None],
) -> LintResult:
    source_digest, checker_digest, env = await concurrently(
        Get(
            Snapshot,
            PathGlobs(
                [
                    "src/ai/backend/**/*.py",
                    "src/ai/backend/**/BUILD",
                ]
            )
        ),
        Get(
            Snapshot,
            PathGlobs(
                [
                    "tools/visibility-checker/Cargo.toml",
                    "tools/visibility-checker/Cargo.lock",
                    "tools/visibility-checker/src/**/*.rs",
                ]
            )
        ),
        Get(EnvironmentVars, EnvironmentVarsRequest(("PATH", "HOME", "CARGO_HOME", "RUSTUP_HOME"))),
    )
    input_digest = await Get(
        Digest,
        MergeDigests((source_digest.digest, checker_digest.digest)),
    )
    result = await Get(
        FallibleProcessResult,
        Process(
            argv=(
                "cargo",
                "run",
                "--quiet",
                "--manifest-path",
                "tools/visibility-checker/Cargo.toml",
                "--",
                "check",
                "--root",
                ".",
                "--quiet",
            ),
            env=dict(env),
            input_digest=input_digest,
            description="Run visibility-checker",
            level=LogLevel.DEBUG,
        ),
    )
    return LintResult(
        exit_code=result.exit_code,
        stdout=result.stdout.decode(),
        stderr=result.stderr.decode(),
        linter_name=request.tool_name,
    )


def rules():
    return (
        *collect_rules(),
        *VisibilityCheckerRequest.rules(),
        *VisibilityCheckerSubsystem.rules(),
    )
