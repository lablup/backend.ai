# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass, replace
from pathlib import PurePath
from typing import Final, Iterable, Mapping

import toml
from pants.backend.python.util_rules.pex_from_targets import (
    InterpreterConstraintsRequest,
)
from pants.core.goals.package import BuiltPackage, BuiltPackageArtifact, PackageFieldSet
from pants.core.goals.run import RunFieldSet, RunInSandboxBehavior, RunRequest
from pants.core.target_types import EnvironmentAwarePackageRequest
from pants.core.util_rules.external_tool import (
    DownloadedExternalTool,
    ExternalToolRequest,
)
from pants.engine.fs import (
    EMPTY_DIGEST,
    CreateDigest,
    Digest,
    DigestContents,
    FileContent,
    MergeDigests,
    Snapshot,
)
from pants.engine.platform import Platform
from pants.engine.process import Process, ProcessResult
from pants.engine.rules import Get, MultiGet, Rule, collect_rules, rule
from pants.engine.target import (
    DependenciesRequest,
    DescriptionField,
    FieldSetsPerTarget,
    FieldSetsPerTargetRequest,
    HydratedSources,
    HydrateSourcesRequest,
    Targets,
)
from pants.engine.unions import UnionRule
from pants.init.plugin_resolver import InterpreterConstraints
from pants.util.logging import LogLevel

from .config import Command, Config, File, Interpreter, LiftConfig
from .subsystems import Science
from .target_types import (
    ScieBinaryNameField,
    ScieDependenciesField,
    ScieFatFlagField,
    ScieLiftSourceField,
    SciePlatformField,
)

logger = logging.getLogger(__name__)

DEFAULT_LIFT_PATH: Final[str] = "lift.toml"
DEFAULT_FAT_LIFT_PATH: Final[str] = "lift-fat.toml"


@dataclass(frozen=True)
class ScieFieldSet(PackageFieldSet, RunFieldSet):
    required_fields = (ScieDependenciesField,)
    run_in_sandbox_behavior = RunInSandboxBehavior.RUN_REQUEST_HERMETIC

    binary_name: ScieBinaryNameField
    description: DescriptionField
    dependencies: ScieDependenciesField
    platforms: SciePlatformField
    lift: ScieLiftSourceField
    fat: ScieFatFlagField


async def _get_interpreter_config(targets: Targets, fat: bool) -> Interpreter:
    # Get the interpreter_constraints for the Pex to determine which version of the Python Standalone to use
    constraints = await Get(
        InterpreterConstraints,
        InterpreterConstraintsRequest([tgt.address for tgt in targets]),
    )
    # TODO: Pull the interpreter_universe from somewhere else (Python Build standalone?)
    minimum_version = constraints.minimum_python_version(["3.8", "3.9", "3.10", "3.11", "3.12"])
    assert minimum_version is not None, "No minimum python version found"
    # Create a toml configuration from the input targets and the minimum_version
    return Interpreter(version=minimum_version, lazy=not fat)


def _get_target_platforms(
    platforms: tuple[str, ...] | None,
    platform_mapping: Mapping[str, str],
    host_platform: Platform,
) -> list[str]:
    if platforms:
        return list(platforms)
    return [platform_mapping.get(host_platform.value, "")]


def _get_files_config(built_packages: Iterable[BuiltPackage]) -> Iterable[File]:
    # Enumerate the files to add to the configuration
    artifact_names = [
        PurePath(artifact.relpath)
        for built_pkg in built_packages
        for artifact in built_pkg.artifacts
        if artifact.relpath is not None
    ]
    return [File(str(path)) for path in artifact_names]


def _contains_pex(built_package: BuiltPackage) -> bool:
    return any(
        artifact.relpath is not None and artifact.relpath.endswith(".pex")
        for artifact in built_package.artifacts
    )


async def _parse_lift_source(source: ScieLiftSourceField) -> Config:
    hydrated_source = await Get(HydratedSources, HydrateSourcesRequest(source))
    digest_contents = await Get(DigestContents, Digest, hydrated_source.snapshot.digest)
    content = digest_contents[0].content.decode("utf-8")
    lift_toml = toml.loads(content)
    logger.error(lift_toml)
    return Config(**lift_toml)


@rule(level=LogLevel.DEBUG)
async def scie_binary(
    science: Science,
    field_set: ScieFieldSet,
    platform: Platform,
) -> BuiltPackage:
    # Grab the dependencies of this target, and build them
    direct_deps = await Get(Targets, DependenciesRequest(field_set.dependencies))

    deps_field_sets = await Get(
        FieldSetsPerTarget, FieldSetsPerTargetRequest(PackageFieldSet, direct_deps)
    )
    built_packages = await MultiGet(
        Get(BuiltPackage, EnvironmentAwarePackageRequest(field_set))
        for field_set in deps_field_sets.field_sets
    )

    # Split the built packages into .pex and non-.pex packages
    pex_packages = [built_pkg for built_pkg in built_packages if _contains_pex(built_pkg)]
    non_pex_packages = [built_pkg for built_pkg in built_packages if not _contains_pex(built_pkg)]

    # Ensure that there is exactly 1 .pex file - reduces complexity of this plugin for now
    assert len(pex_packages) == 1, f"Expected exactly 1 .pex package, but found {len(pex_packages)}"
    pex_package = pex_packages[0]

    # Ensure there is only 1 .pex artifact in the .pex package
    pex_artifacts = [
        artifact
        for artifact in pex_package.artifacts
        if artifact.relpath is not None and artifact.relpath.endswith(".pex")
    ]
    assert (
        len(pex_artifacts) == 1
    ), f"Expected exactly 1 .pex artifact, but found {len(pex_artifacts)}"
    pex_artifact = pex_artifacts[0]
    assert pex_artifact.relpath is not None, "Expected single .pex artifact to have a relpath"
    pex_artifact_path = PurePath(pex_artifact.relpath)

    # Prepare the configuration toml for the Science tool
    binary_name = field_set.binary_name.value or field_set.address.target_name
    assert science.default_url_platform_mapping is not None
    target_platforms = _get_target_platforms(
        field_set.platforms.value, science.default_url_platform_mapping, platform
    )
    interpreter_config = await _get_interpreter_config(direct_deps, field_set.fat.value)
    # TODO: This might be better solved by using the `:target_name` syntax and letting downstream handle it
    files_config = _get_files_config(built_packages)

    # Create a toml configuration from the input targets and the minimum_version, and place that into a Digest for later usage
    generated_config = Config(
        lift=LiftConfig(
            name=binary_name,
            description=field_set.description.value or "",
            platforms=list(target_platforms),
            interpreters=[interpreter_config],
            files=list(files_config),
            commands=[Command(exe="#{cpython:python}", args=[f"{{{ pex_artifact_path }}}"])],
        )
    )

    parsed_config: Config | None = None
    lift_digest = EMPTY_DIGEST
    lift_path = DEFAULT_LIFT_PATH
    if field_set.fat:
        lift_path = DEFAULT_FAT_LIFT_PATH
    if field_set.lift.value is not None:
        # If the user specified a lift.toml file, then use that instead of the generated one
        parsed_config = await _parse_lift_source(field_set.lift)
        assert field_set.lift.file_path is not None
        lift_path = field_set.lift.file_path

    # TODO: Merge the parsed config with the generated config, rather than replacing it
    config = parsed_config or generated_config

    config_content = toml.dumps(asdict(config)).encode()
    lift_digest = await Get(Digest, CreateDigest([FileContent(lift_path, config_content)]))

    # Download the Science tool for this platform
    downloaded_tool = await Get(
        DownloadedExternalTool, ExternalToolRequest, science.get_request(platform)
    )

    # Put the dependencies and toml configuration into a digest
    input_digest = await Get(
        Digest,
        MergeDigests(
            (
                lift_digest,
                downloaded_tool.digest,
                *(pkg.digest for pkg in non_pex_packages),
                pex_package.digest,
            )
        ),
    )

    # The output files are based on the config.lift.name key and each of the platforms (if specified), otherwise just the config.lift.name for native-only
    output_files = [config.lift.name] + [
        f"{config.lift.name}-{platform}" for platform in config.lift.platforms
    ]

    # If any of the config filenames start with `:` then add a filemapping command line arg in the form --file NAME=LOCATION
    file_mappings = [
        f"--file {file.name}={pex_artifact_path}"
        for file in config.lift.files
        if file.name.startswith(":")
    ]
    # Split each file mapping into a list of arguments
    file_mappings = [arg for mapping in file_mappings for arg in mapping.split(" ")]
    logger.warning(file_mappings)

    # Run science to generate the scie binaries (depending on the `platforms` setting)
    argv = (
        downloaded_tool.exe,
        "lift",
        *file_mappings,
        "build",
        "--use-platform-suffix" if config.lift.platforms else "",
        lift_path,
    )
    process = Process(
        argv=argv,
        input_digest=input_digest,
        description="Run science on the input digests",
        output_files=output_files,
        level=LogLevel.DEBUG,
    )

    result = await Get(ProcessResult, Process, process)
    snapshot = await Get(
        Snapshot,
        Digest,
        result.output_digest,
    )

    return BuiltPackage(
        result.output_digest,
        artifacts=tuple(BuiltPackageArtifact(file) for file in snapshot.files),
    )


@rule
async def run_scie_binary(field_set: ScieFieldSet) -> RunRequest:
    """After packaging, the scie-jump plugin will place the executable in a location like this:
    dist/{binary name}

    {binary name} will default to `target_name`, but can be modified on the `scie_binary` target.
    """

    binary = await Get(BuiltPackage, PackageFieldSet, field_set)
    assert len(binary.artifacts) == 1, "`scie_binary` should only generate one output package"
    artifact = binary.artifacts[0]
    assert artifact.relpath is not None
    return RunRequest(digest=binary.digest, args=(os.path.join("{chroot}", artifact.relpath),))


def rules() -> Iterable[Rule | UnionRule]:
    return (
        *collect_rules(),
        UnionRule(PackageFieldSet, ScieFieldSet),
        *ScieFieldSet.rules(),
    )
