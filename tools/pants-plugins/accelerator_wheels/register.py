"""
Custom Pants plugin to handle dependency inference for accelerator packages.

This plugin modifies the default dependency inference behavior to exclude
Backend.AI core dependencies (src/ai/backend/*) from accelerator packages
(src/ai/backend/accelerator/*), allowing accelerators to be built as
standalone wheels without pulling in the entire Backend.AI codebase.
"""
from __future__ import annotations

import logging

# Import Pants Python backend rules for dependency inference
from pants.backend.python.dependency_inference.rules import (
    PythonImportDependenciesInferenceFieldSet,  # FieldSet for Python import dependency inference
    InferPythonImportDependencies,  # Request type for standard Python import dependency inference
)
from pants.backend.python.dependency_inference.subsystem import (
    PythonInferSubsystem,  # Configuration subsystem for Python dependency inference
)
from pants.backend.python.subsystems.setup import PythonSetup  # Global Python setup configuration
from pants.backend.python.target_types import PythonSourceTarget  # Python source file target type
from pants.engine.addresses import Address  # Target address type for dependency graph
from pants.engine.rules import Get, collect_rules, rule  # Core Pants rule engine primitives
from pants.engine.target import (
    InferDependenciesRequest,  # Base request type for dependency inference
    InferredDependencies,  # Result type containing inferred dependencies
    Tags,  # Target tag field for classification
    Target,  # Base target type
    TransitivelyExcludeDependencies,  # Result type for dependencies to exclude transitively
    TransitivelyExcludeDependenciesRequest,  # Request type for transitive exclusion
)
from pants.engine.unions import UnionRule  # Register custom rules in the rule graph

log = logging.getLogger(__name__)


# Exclusion predicate: Returns True if dependency should be excluded from accelerator packages
# Excludes all Backend.AI core packages (src/ai/backend/*) except accelerator packages themselves
# This allows accelerators to depend on each other but not on the main Backend.AI codebase
should_exclude = lambda dep: dep.spec_path.startswith("src/ai/backend") and not dep.spec_path.startswith("src/ai/backend/accelerator")


async def _common_exclude_logic(
    request: TransitivelyExcludeDependenciesRequest,
    inferred_deps: InferredDependencies,
) -> TransitivelyExcludeDependencies:
    """
    Helper function to filter and exclude Backend.AI core dependencies.

    Iterates through inferred dependencies and marks Backend.AI core packages
    (except accelerators) for exclusion. Logs each decision for debugging:
    - '!' prefix: dependency excluded
    - '^' prefix: dependency kept

    Args:
        request: The exclusion request context with target information
        inferred_deps: Dependencies inferred by standard Python import analysis

    Returns:
        TransitivelyExcludeDependencies containing addresses to exclude from the build graph
    """
    sb = f"_common_exclude_logic({request.__class__}, {request.field_set.address}): inferred:\n"
    excluded_dependencies: list[Address] = []

    # Iterate through all inferred dependencies and filter based on exclusion predicate
    for dep in inferred_deps.include:
        if should_exclude(dep):
            sb += f"    ! {dep}\n"  # Mark as excluded
            excluded_dependencies.append(dep)
        else:
            sb += f"    ^ {dep}\n"  # Mark as kept
    log.debug(sb)

    # Return the list of dependencies to exclude transitively from the build graph
    return TransitivelyExcludeDependencies(excluded_dependencies)


class FakeInferPythonImportDependenciesFieldSet(PythonImportDependenciesInferenceFieldSet):
    """
    FieldSet for identifying accelerator Python source files.

    Extends the standard PythonImportDependenciesInferenceFieldSet to target
    only files tagged with "accelerator". This allows the custom inference rule
    to selectively apply only to accelerator packages.
    """

    @classmethod
    def is_applicable(cls, target: Target) -> bool:
        """
        Determines if this FieldSet applies to the given target.

        Returns True only if:
        1. Target is a PythonSourceTarget (Python source file)
        2. Target has tags defined
        3. Tags include "accelerator"

        This filtering ensures the custom dependency inference only runs for
        accelerator packages, not the entire codebase.
        """
        tags = target.field_values.get(Tags)
        should_continue = isinstance(target, PythonSourceTarget) and tags.value and "accelerator" in tags.value
        return should_continue


class FakeInferPythonImportDependencies(InferDependenciesRequest):
    """
    Custom dependency inference request for accelerator packages.

    This class acts as a union member (registered via UnionRule below) that
    extends the standard InferDependenciesRequest. When Pants encounters targets
    matching FakeInferPythonImportDependenciesFieldSet, it dispatches to the
    corresponding rule to perform custom dependency inference.
    """
    infer_from = FakeInferPythonImportDependenciesFieldSet


@rule
async def fake_infer_accelerator_python_import_dependencies(
    request: FakeInferPythonImportDependencies,
    python_infer_subsystem: PythonInferSubsystem,
    python_setup: PythonSetup,
) -> InferredDependencies:
    """
    Custom rule that modifies dependency inference for accelerator packages.

    This rule intercepts dependency inference for targets tagged with "accelerator"
    and excludes Backend.AI core dependencies from the build graph. It enables
    building accelerator packages as standalone wheels without requiring the
    entire Backend.AI monorepo.

    Flow:
    1. Delegate to standard Python import dependency inference (await Get)
    2. Filter inferred dependencies using _common_exclude_logic
    3. Return empty includes but populated excludes, effectively removing
       Backend.AI core packages from the dependency graph

    Args:
        request: The custom inference request for accelerator packages
        python_infer_subsystem: Configuration for Python dependency inference
        python_setup: Global Python configuration

    Returns:
        InferredDependencies with empty includes and Backend.AI core exclusions
    """
    # Use 'await Get' to request standard Python import dependency inference
    # This is the core Pants rules API pattern for requesting types dynamically
    inferred_deps = await Get(
        InferredDependencies,
        InferPythonImportDependencies(request.field_set),
    )

    # Filter the inferred dependencies to exclude Backend.AI core packages
    result = await _common_exclude_logic(request, inferred_deps)

    # Return InferredDependencies with no includes but with exclusions
    # This effectively removes Backend.AI core dependencies from the build graph
    return InferredDependencies([], exclude=[*result])


def rules():
    """
    Register all rules and union members defined in this plugin.

    Returns:
        List containing:
        1. All @rule decorated functions via collect_rules()
        2. UnionRule registering FakeInferPythonImportDependencies as an
           implementation of InferDependenciesRequest

    The UnionRule enables Pants' dependency inference system to discover and
    invoke our custom rule when processing accelerator-tagged targets. This is
    the extensibility mechanism that allows plugins to inject custom behavior
    without modifying core Pants code.
    """
    return [
        *collect_rules(),  # Auto-collects all @rule decorated functions in this module
        UnionRule(InferDependenciesRequest, FakeInferPythonImportDependencies),  # Register as union member
    ]
