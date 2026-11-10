from __future__ import annotations

import ast
from pathlib import Path

import pytest

# Imported so the checked packages are present in the test sandbox.
import ai.backend.manager.dependencies.processing.bgtask_registry
import ai.backend.manager.event_dispatcher.dispatch
import ai.backend.manager.sokovan

MANAGER_ROOT = Path(ai.backend.manager.sokovan.__file__).parent.parent
SERVICES_PACKAGE = "ai.backend.manager.services"


def _processor_imports(path: Path) -> list[str]:
    found: list[str] = []
    for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
            modules = [node.module] + [f"{node.module}.{alias.name}" for alias in node.names]
        for module in modules:
            parts = module.split(".")
            if module.startswith(f"{SERVICES_PACKAGE}.") and "processors" in parts:
                found.append(module)
    return found


@pytest.mark.parametrize("package", ["event_dispatcher", "bgtask", "sokovan"])
def test_internal_callers_do_not_import_processors(package: str) -> None:
    sources = sorted((MANAGER_ROOT / package).rglob("*.py"))
    assert sources

    violations = {
        str(path.relative_to(MANAGER_ROOT)): imports
        for path in sources
        if (imports := _processor_imports(path))
    }

    assert violations == {}
