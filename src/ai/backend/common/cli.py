import functools
import os
import re
import sys
from decimal import Decimal
from enum import Enum
from importlib import import_module
from types import FunctionType
from typing import Any, Optional, Type, Union

import click


def wrap_method(method):
    @functools.wraps(method)
    def wrapped(self, *args, **kwargs):
        return method(self._impl, *args, **kwargs)

    return wrapped


class LazyClickMixin:
    """
    Click's documentations says "supports lazy loading of subcommands at runtime",
    but there is no actual examples and how-tos as indicated by the issue:
    https://github.com/pallets/click/issues/945

    This class fills the gap by binding the methods of original Click classes to
    a wrapper that lazily loads the underlying Click object.
    """

    _import_name: str
    _loaded_impl: Optional[Union[click.Command, click.Group]]

    def __init__(self, *, import_name, **kwargs):
        self._import_name = import_name
        self._loaded_impl = None
        super().__init__(**kwargs)
        for key, val in vars(type(self).__mro__[2]).items():
            if key.startswith("__"):
                continue
            if isinstance(val, FunctionType):
                setattr(self, key, wrap_method(val).__get__(self, self.__class__))

    @property
    def _impl(self):
        if self._loaded_impl:
            return self._loaded_impl
        # Load when first invoked.
        module, name = self._import_name.split(":", 1)
        self._loaded_impl = getattr(import_module(module), name)
        return self._loaded_impl


class LazyGroup(LazyClickMixin, click.Group):
    pass


class EnumChoice(click.Choice):
    enum: Type[Enum]

    def __init__(self, enum: Type[Enum]):
        enum_members = [e.name for e in enum]
        super().__init__(enum_members)
        self.enum = enum

    def convert(self, value: Any, param, ctx):
        if isinstance(value, self.enum):
            # for default value, it is already the enum type.
            return next(e for e in self.enum if e == value)
        value = super().convert(value, param, ctx)
        return next(k for k in self.enum.__members__.keys() if k == value)

    def get_metavar(self, param):
        name = self.enum.__name__
        name = re.sub(r"([A-Z\d]+)([A-Z][a-z])", r"\1_\2", name)
        name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
        return name.upper()


class MinMaxRangeParamType(click.ParamType):
    name = "min-max decimal range"

    def convert(self, value, param, ctx):
        try:
            left, _, right = value.partition(":")
            if left:
                left = Decimal(left)
            else:
                left = None
            if right:
                right = Decimal(right)
            else:
                right = None
            return left, right
        except (ArithmeticError, ValueError):
            self.fail(f"{value!r} contains an invalid number", param, ctx)

    def get_metavar(self, param):
        return "MIN:MAX"


MinMaxRange = MinMaxRangeParamType()


def get_completion_command(prog_name: str) -> click.Command:
    """
    Create a completion command for shell auto-completion.

    Args:
        prog_name: The name of the program (e.g., 'backend.ai', 'manager', 'agent')
    """

    @click.command()
    @click.option(
        "--shell",
        type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
        default=None,
        help="The shell type. If not provided, it will be auto-detected.",
    )
    @click.option(
        "--show",
        is_flag=True,
        help="Show the completion script instead of installing it.",
    )
    def completion(shell: Optional[str], show: bool) -> None:
        """
        Install or show shell completion script.

        This command helps you set up tab completion for this CLI.
        """
        # Auto-detect shell if not provided
        if not shell:
            shell_env = os.environ.get("SHELL", "")
            if "bash" in shell_env:
                shell = "bash"
            elif "zsh" in shell_env:
                shell = "zsh"
            elif "fish" in shell_env:
                shell = "fish"
            else:
                click.echo(
                    "Could not detect shell type. Please specify --shell option.",
                    err=True,
                )
                sys.exit(1)

        shell = shell.lower()
        env_var = f"_{prog_name.upper().replace('.', '_').replace('-', '_')}_COMPLETE"

        if show:
            # Show instructions for manual setup
            click.echo(f"# Shell completion for {prog_name} ({shell})")
            click.echo()
            click.echo("To enable shell completion, run one of the following commands:")
            click.echo()

            if shell == "bash":
                click.echo("# For Bash:")
                click.echo(f'eval "$({env_var}=bash_source {prog_name})"')
                click.echo()
                click.echo("# Or add to ~/.bashrc:")
                click.echo(f"echo 'eval \"$({env_var}=bash_source {prog_name})\"' >> ~/.bashrc")
            elif shell == "zsh":
                click.echo("# For Zsh:")
                click.echo(f'eval "$({env_var}=zsh_source {prog_name})"')
                click.echo()
                click.echo("# Or add to ~/.zshrc:")
                click.echo(f"echo 'eval \"$({env_var}=zsh_source {prog_name})\"' >> ~/.zshrc")
            elif shell == "fish":
                click.echo("# For Fish:")
                click.echo(f"{env_var}=fish_source {prog_name} | source")
                click.echo()
                click.echo("# Or save to config file:")
                click.echo(
                    f"{env_var}=fish_source {prog_name} > ~/.config/fish/completions/{prog_name}.fish"
                )
        else:
            # Install the completion script
            click.echo(f"Installing {shell} completion for {prog_name}...")
            click.echo()

            if shell == "bash":
                rc_file = os.path.expanduser("~/.bashrc")
                completion_line = f'eval "$({env_var}=bash_source {prog_name})"'
            elif shell == "zsh":
                rc_file = os.path.expanduser("~/.zshrc")
                completion_line = f'eval "$({env_var}=zsh_source {prog_name})"'
            elif shell == "fish":
                fish_config_dir = os.path.expanduser("~/.config/fish/completions")
                os.makedirs(fish_config_dir, exist_ok=True)
                completion_file = os.path.join(fish_config_dir, f"{prog_name}.fish")

                # Generate and write fish completion script
                import subprocess

                result = subprocess.run(
                    [prog_name],
                    env={**os.environ, env_var: "fish_source"},
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0 and result.stdout:
                    with open(completion_file, "w") as f:
                        f.write(result.stdout)
                    click.echo(f"✓ Completion script written to: {completion_file}")
                    click.echo()
                    click.echo("Installation complete!")
                    click.echo()
                    click.echo("To activate completion, restart your shell or run:")
                    click.echo("  exec fish")
                else:
                    click.echo(
                        "Could not generate completion script. Using eval method instead.",
                        err=True,
                    )
                    rc_file = os.path.expanduser("~/.config/fish/config.fish")
                    completion_line = f"{env_var}=fish_source {prog_name} | source"
                return
            else:
                click.echo(f"Unsupported shell: {shell}", err=True)
                sys.exit(1)

            # Add completion line to rc file
            if os.path.exists(rc_file):
                with open(rc_file, "r") as f:
                    rc_content = f.read()

                if completion_line not in rc_content:
                    with open(rc_file, "a") as f:
                        f.write(f"\n# {prog_name} completion\n")
                        f.write(f"{completion_line}\n")
                    click.echo(f"✓ Added completion to: {rc_file}")
                else:
                    click.echo(f"✓ Completion already configured in: {rc_file}")
            else:
                with open(rc_file, "w") as f:
                    f.write(f"# {prog_name} completion\n")
                    f.write(f"{completion_line}\n")
                click.echo(f"✓ Created {rc_file} with completion configuration")

            click.echo()
            click.echo("Installation complete!")
            click.echo()
            click.echo("To activate completion in your current shell, run:")
            click.echo(f"  source {rc_file}")
            click.echo()
            click.echo("Or start a new shell session.")

    return completion
