"""Tests for RBAC action registry completeness."""

import importlib
import inspect
import pkgutil

import ai.backend.manager.actions.action as action_pkg
from ai.backend.manager.actions.action.rbac import BaseRBACAction
from ai.backend.manager.actions.action.rbac_registry import RBAC_ACTION_REGISTRY


def _import_all_rbac_modules() -> None:
    """Import all rbac_* modules to ensure __subclasses__() discovers everything."""
    package_path = action_pkg.__path__
    for module_info in pkgutil.iter_modules(package_path):
        if module_info.name.startswith("rbac_"):
            importlib.import_module(f"{action_pkg.__name__}.{module_info.name}")


def _collect_concrete_subclasses(base: type) -> set[type[BaseRBACAction]]:
    """Recursively collect all concrete (non-abstract) subclasses."""
    result: set[type[BaseRBACAction]] = set()
    for sub in base.__subclasses__():
        if not inspect.isabstract(sub):
            result.add(sub)
        result.update(_collect_concrete_subclasses(sub))
    return result


# Ensure all rbac_* modules are imported before any test runs.
_import_all_rbac_modules()


class TestRBACRegistryCompleteness:
    def test_all_concrete_subclasses_are_registered(self) -> None:
        concrete_subclasses = _collect_concrete_subclasses(BaseRBACAction)
        registry_set = set(RBAC_ACTION_REGISTRY)
        missing = concrete_subclasses - registry_set
        assert not missing, (
            f"The following BaseRBACAction subclasses are not in RBAC_ACTION_REGISTRY: "
            f"{', '.join(cls.__name__ for cls in sorted(missing, key=lambda c: c.__name__))}"
        )

    def test_registry_has_no_duplicates(self) -> None:
        seen: set[type[BaseRBACAction]] = set()
        duplicates: list[str] = []
        for cls in RBAC_ACTION_REGISTRY:
            if cls in seen:
                duplicates.append(cls.__name__)
            seen.add(cls)
        assert not duplicates, f"Duplicate entries in RBAC_ACTION_REGISTRY: {', '.join(duplicates)}"

    def test_registry_contains_only_base_rbac_action_subclasses(self) -> None:
        non_subclasses: list[str] = []
        for entry in RBAC_ACTION_REGISTRY:
            cls: type = entry
            if not issubclass(cls, BaseRBACAction):
                non_subclasses.append(cls.__name__)
        assert not non_subclasses, (
            f"Non-BaseRBACAction entries in RBAC_ACTION_REGISTRY: {', '.join(non_subclasses)}"
        )
