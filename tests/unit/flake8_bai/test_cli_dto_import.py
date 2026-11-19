from collections.abc import Callable

type Lint = Callable[[str, str], list[tuple[int, str]]]

CLI_COMMANDS = "src/ai/backend/client/cli/v2/entity_share/commands.py"


class TestCliDtoImportRule:
    def test_module_level_dto_import_fails(self, lint: Lint) -> None:
        source = """
            import click
            from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
            import ai.backend.common.dto.manager.v2.user.request
            from ai.backend.common import dto
        """
        assert lint(CLI_COMMANDS, source) == [(3, "BAI204"), (4, "BAI204"), (5, "BAI204")]

    def test_dto_import_in_module_level_block_fails(self, lint: Lint) -> None:
        source = """
            try:
                from ai.backend.common.dto.manager.v2.user.request import CreateUserInput
            except ImportError:
                pass
        """
        assert lint(CLI_COMMANDS, source) == [(3, "BAI204")]

    def test_dto_import_in_command_function_passes(self, lint: Lint) -> None:
        source = """
            import click

            @click.command()
            def share() -> None:
                from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
        """
        assert lint(CLI_COMMANDS, source) == []

    def test_dto_import_under_type_checking_passes(self, lint: Lint) -> None:
        source = """
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                from ai.backend.common.dto.manager.v2.user.request import CreateUserInput
        """
        assert lint(CLI_COMMANDS, source) == []

    def test_other_module_level_import_passes(self, lint: Lint) -> None:
        source = """
            import click
            from ai.backend.common.types import SessionId
            from ai.backend.common.dto_helpers import parse
        """
        assert lint(CLI_COMMANDS, source) == []

    def test_dto_import_outside_cli_v2_passes(self, lint: Lint) -> None:
        source = """
            from ai.backend.common.dto.manager.v2.user.request import CreateUserInput
        """
        assert lint("src/ai/backend/client/v2/domains_v2/user.py", source) == []
