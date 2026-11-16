"""Check `freeze_release_version.py`. Run it directly: `python scripts/test_freeze_release_version.py`.

`/scripts/` is outside the pants source tree, so this cannot be a pants test.
"""

import ast
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType

SCRIPT = Path(__file__).with_name("freeze_release_version.py")
VERSION = "26.4.0"

M = "from ai.backend.common.meta import "
KEPT = M + "BackendAIConfigMeta, ConfigExample\n"

CASES = [
    (
        "standalone import from meta",
        M + "NEXT_RELEASE_VERSION\nx = NEXT_RELEASE_VERSION\n",
        'x = "26.4.0"\n',
    ),
    (
        "standalone import from meta.meta",
        "from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION\nx = NEXT_RELEASE_VERSION\n",
        'x = "26.4.0"\n',
    ),
    (
        "indented standalone import",
        "def f():\n    from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION\n"
        "    return NEXT_RELEASE_VERSION\n",
        'def f():\n    return "26.4.0"\n',
    ),
    (
        "one-line import, placeholder first",
        M + "NEXT_RELEASE_VERSION, BackendAIConfigMeta, ConfigExample\n",
        KEPT,
    ),
    (
        "one-line import, placeholder in the middle",
        M + "BackendAIConfigMeta, NEXT_RELEASE_VERSION, ConfigExample\n",
        KEPT,
    ),
    (
        "one-line import, placeholder last",
        M + "BackendAIConfigMeta, ConfigExample, NEXT_RELEASE_VERSION\n",
        KEPT,
    ),
    (
        "one-line import with a trailing comment",
        M + "BackendAIConfigMeta, ConfigExample, NEXT_RELEASE_VERSION  # noqa\n",
        M + "BackendAIConfigMeta, ConfigExample  # noqa\n",
    ),
    (
        "parenthesized one-line import",
        M + "(NEXT_RELEASE_VERSION, BackendAIConfigMeta, ConfigExample)\n",
        KEPT,
    ),
    (
        "no space before the parenthesis",
        "from ai.backend.common.meta import(NEXT_RELEASE_VERSION, BackendAIConfigMeta, ConfigExample)\n",
        KEPT,
    ),
    (
        "backslash continuation",
        M + "\\\n    NEXT_RELEASE_VERSION, BackendAIConfigMeta, ConfigExample\n",
        KEPT,
    ),
    (
        "multi-line import",
        M
        + "(\n    NEXT_RELEASE_VERSION,\n    BackendAIConfigMeta,\n    ConfigExample,\n)\nx = 1\n",
        KEPT + "x = 1\n",
    ),
    (
        "multi-line import, placeholder last without a comma",
        M + "(\n    BackendAIConfigMeta,\n    ConfigExample,\n    NEXT_RELEASE_VERSION\n)\n",
        KEPT,
    ),
    (
        "multi-line import, comment after the opening parenthesis",
        M
        + "(  # noqa\n    NEXT_RELEASE_VERSION,\n    BackendAIConfigMeta,\n    ConfigExample,\n)\n",
        M + "BackendAIConfigMeta, ConfigExample  # noqa\n",
    ),
    (
        "multi-line import, comment on the placeholder item",
        M
        + "(\n    NEXT_RELEASE_VERSION,  # noqa: F401\n    BackendAIConfigMeta,\n    ConfigExample,\n)\n",
        M + "BackendAIConfigMeta, ConfigExample  # noqa: F401\n",
    ),
    (
        "multi-line import, first item on the opening line",
        M + "(NEXT_RELEASE_VERSION,\n    BackendAIConfigMeta,\n    ConfigExample)\n",
        KEPT,
    ),
    (
        "multi-line import, closing parenthesis on the last item, code after it",
        M + "(\n    NEXT_RELEASE_VERSION,\n    BackendAIConfigMeta,\n    ConfigExample)\n"
        "x = NEXT_RELEASE_VERSION\n",
        KEPT + 'x = "26.4.0"\n',
    ),
    (
        "multi-line import of the placeholder alone, with a comment line",
        M + "(\n    NEXT_RELEASE_VERSION,\n    # add names here\n)\nx = 1\n",
        "x = 1\n",
    ),
    (
        "multi-line import, comments on a kept item and the closing parenthesis",
        M
        + "(\n    NEXT_RELEASE_VERSION,\n    BackendAIConfigMeta,  # noqa: F401\n"
        + "    ConfigExample,\n)  # keep\n",
        M + "BackendAIConfigMeta, ConfigExample  # noqa: F401  # keep\n",
    ),
    (
        "CRLF line endings",
        M + "NEXT_RELEASE_VERSION, ConfigExample\r\nx = NEXT_RELEASE_VERSION\r\n",
        M + 'ConfigExample\r\nx = "26.4.0"\r\n',
    ),
    (
        "two imports in one file",
        M
        + "NEXT_RELEASE_VERSION, ConfigExample\n"
        + "from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION\n"
        + "x = NEXT_RELEASE_VERSION\n",
        M + 'ConfigExample\nx = "26.4.0"\n',
    ),
    (
        "import in a block with another statement",
        "try:\n    from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION\n"
        "    x = NEXT_RELEASE_VERSION\nexcept ImportError:\n    pass\n",
        'try:\n    x = "26.4.0"\nexcept ImportError:\n    pass\n',
    ),
    (
        "other names keep their aliases",
        M + "NEXT_RELEASE_VERSION, ConfigExample as Example\n",
        M + "ConfigExample as Example\n",
    ),
    (
        "import without the placeholder, placeholder in its comment",
        M + "ConfigExample  # Added in NEXT_RELEASE_VERSION\n",
        M + "ConfigExample  # Added in 26.4.0\n",
    ),
    (
        "placeholder item outside an import",
        "versions = [\n    NEXT_RELEASE_VERSION,\n]\n",
        'versions = [\n    "26.4.0",\n]\n',
    ),
    (
        "f-string and comment",
        'msg = f"Added in {NEXT_RELEASE_VERSION}."  # Part of: NEXT_RELEASE_VERSION\n',
        'msg = f"Added in 26.4.0."  # Part of: 26.4.0\n',
    ),
]

REJECTED = [
    ("alias", "from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION as NRV\n"),
    (
        "alias in a multi-line import",
        M + "(\n    NEXT_RELEASE_VERSION as NRV,\n    ConfigExample,\n)\n",
    ),
    ("another module", "from foo import (\n    NEXT_RELEASE_VERSION,\n)\n"),
    ("relative import", "from .meta import NEXT_RELEASE_VERSION\n"),
    (
        "only statement of a try block",
        "try:\n    from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION\n"
        "except ImportError:\n    pass\n",
    ),
    (
        "only statement of a function",
        "def f():\n    from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION\n",
    ),
    (
        "on the line of a block header",
        "if x: from ai.backend.common.meta import NEXT_RELEASE_VERSION, A\n",
    ),
    ("statement after it on the line", M + "NEXT_RELEASE_VERSION, ConfigExample; y = 1\n"),
    ("statement before it on the line", "y = 1; " + M + "NEXT_RELEASE_VERSION, ConfigExample\n"),
    (
        "two imports on one line",
        M + "ConfigExample; from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION\n",
    ),
]


def check_freeze_version() -> None:
    meta = "src/ai/backend/common/meta/"
    excluded = {
        meta + "meta.py": 'NEXT_RELEASE_VERSION = "26.5.0"\n',
        meta + "__init__.py": "from .meta import NEXT_RELEASE_VERSION\n",
    }
    frozen = {"src/a.py": M + "NEXT_RELEASE_VERSION\nx = NEXT_RELEASE_VERSION\n"}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for path, text in {**excluded, **frozen}.items():
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_text(text)

        unsupported = {"src/b.py": "from .meta import NEXT_RELEASE_VERSION\n"}
        (root / "src/b.py").write_text(unsupported["src/b.py"])
        result = run_script(root)
        assert result.returncode == 1, f"unsupported import: exited {result.returncode}"
        assert "src/b.py: line 1" in result.stderr, f"unsupported import: {result.stderr!r}"
        for path, text in {**excluded, **frozen, **unsupported}.items():
            assert (root / path).read_text() == text, f"unsupported import: {path} was written"

        (root / "src/b.py").unlink()
        result = run_script(root)
        assert result.returncode == 0, f"exited {result.returncode}: {result.stderr}"
        for path, text in excluded.items():
            assert (root / path).read_text() == text, f"{path} was written"
        assert (root / "src/a.py").read_text() == 'x = "26.4.0"\n'


def run_script(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT.resolve()), VERSION], cwd=cwd, capture_output=True, text=True
    )


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("freeze_release_version", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_module()
    for name, source, expected in CASES:
        actual = module.freeze_file(source, VERSION)
        assert actual == expected, f"{name}: expected {expected!r}, got {actual!r}"
        ast.parse(actual)
    for name, source in REJECTED:
        try:
            module.freeze_file(source, VERSION)
        except module.UnsupportedImportError:
            continue
        raise AssertionError(f"{name}: accepted {source!r}")
    check_freeze_version()
    print(f"ok: {len(CASES) + len(REJECTED)} cases and the file walk")


if __name__ == "__main__":
    main()
