import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

type Lint = Callable[[str, str], list[tuple[int, str]]]

GROUP_SOURCE = """
    import click

    from ai.backend.common.cli import LazyGroup

    @click.group()
    def main() -> None: ...

    @main.group(cls=LazyGroup, import_name="{import_name}")
    def config() -> None: ...
"""


@pytest.fixture
def cli_main(tmp_path: Path) -> str:
    """A CLI entry module beside `ai/backend/agent/cli/config.py` and `ai/backend/agent/cli/kernel/`."""
    cli_dir = tmp_path / "src" / "ai" / "backend" / "agent" / "cli"
    (cli_dir / "kernel").mkdir(parents=True)
    (cli_dir / "config.py").write_text(
        textwrap.dedent("""
            import click

            try:
                from tomllib import loads
            except ImportError:
                loads = None

            @click.group()
            def cli() -> None: ...
        """)
    )
    (cli_dir / "kernel" / "__init__.py").write_text(
        "from ai.backend.agent.cli.kernel.base import *\n"
    )
    return str(cli_dir / "__main__.py")


class TestLazyGroupTargetRule:
    def test_missing_module_fails(self, lint: Lint, cli_main: str) -> None:
        source = GROUP_SOURCE.format(import_name="ai.backend.agent.cli.auth:cli")
        assert lint(cli_main, source) == [(9, "BAI401")]

    def test_missing_name_fails(self, lint: Lint, cli_main: str) -> None:
        source = GROUP_SOURCE.format(import_name="ai.backend.agent.cli.config:main")
        assert lint(cli_main, source) == [(9, "BAI401")]

    def test_import_name_without_attribute_fails(self, lint: Lint, cli_main: str) -> None:
        source = GROUP_SOURCE.format(import_name="ai.backend.agent.cli.config")
        assert lint(cli_main, source) == [(9, "BAI401")]

    def test_lazy_group_call_with_missing_module_fails(self, lint: Lint, cli_main: str) -> None:
        source = """
            from ai.backend.common.cli import LazyGroup

            group = LazyGroup(name="auth", import_name="ai.backend.agent.cli.auth:cli")
        """
        assert lint(cli_main, source) == [(4, "BAI401")]

    def test_existing_module_and_name_pass(self, lint: Lint, cli_main: str) -> None:
        source = GROUP_SOURCE.format(import_name="ai.backend.agent.cli.config:cli")
        assert lint(cli_main, source) == []

    def test_name_bound_in_try_passes(self, lint: Lint, cli_main: str) -> None:
        source = GROUP_SOURCE.format(import_name="ai.backend.agent.cli.config:loads")
        assert lint(cli_main, source) == []

    def test_package_with_star_import_passes(self, lint: Lint, cli_main: str) -> None:
        source = GROUP_SOURCE.format(import_name="ai.backend.agent.cli.kernel:cli")
        assert lint(cli_main, source) == []

    def test_import_name_of_other_group_class_passes(self, lint: Lint, cli_main: str) -> None:
        source = """
            import click

            @click.group(cls=click.Group, import_name="ai.backend.agent.cli.auth:cli")
            def auth() -> None: ...
        """
        assert lint(cli_main, source) == []
