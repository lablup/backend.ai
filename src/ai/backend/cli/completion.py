from __future__ import annotations

import os
import subprocess
import sys
from typing import Optional

import click


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
                with open(rc_file) as f:
                    content = f.read()

                if completion_line in content:
                    click.echo(f"✓ Completion already configured in {rc_file}")
                else:
                    with open(rc_file, "a") as f:
                        f.write(f"\n# Backend.AI completion\n{completion_line}\n")
                    click.echo(f"✓ Added completion line to {rc_file}")
            else:
                with open(rc_file, "w") as f:
                    f.write(f"# Backend.AI completion\n{completion_line}\n")
                click.echo(f"✓ Created {rc_file} with completion line")

            click.echo()
            click.echo("Installation complete!")
            click.echo()
            click.echo("To activate completion, restart your shell or run:")
            if shell == "bash":
                click.echo(f"  source {rc_file}")
            elif shell == "zsh":
                click.echo(f"  source {rc_file}")

    return completion
