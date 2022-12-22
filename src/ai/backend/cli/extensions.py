import os
import signal
import sys

import click
from click.exceptions import Abort, ClickException

from .types import ExitCode


class InterruptAwareCommandMixin(click.BaseCommand):
    """
    Replace the main() method to support proper exit-codes
    for interruptions on Windows and POSIX platforms.
    Using this, interrupting the command will let the shell
    know that the execution is also interrupted instead of
    continuing the shell/batch script.
    """

    def main(self, *args, **kwargs):
        try:
            _interrupted = False
            kwargs.pop("standalone_mode", None)
            kwargs.pop("prog_name", None)
            super().main(
                *args,
                standalone_mode=False,
                prog_name="backend.ai",
                **kwargs,
            )
        except KeyboardInterrupt:
            # For interruptions outside the Click's exception handling block.
            print("Interrupted!", end="", file=sys.stderr)
            sys.stderr.flush()
            _interrupted = True
        except Abort as e:
            # Click wraps unhandled KeyboardInterrupt with a plain
            # sys.exit(1) call and prints "Aborted!" message
            # (which would look non-sense to users).
            # This is *NOT* what we want.
            # Instead of relying on Click, mark the _interrupted
            # flag to perform our own exit routines.
            if isinstance(e.__context__, KeyboardInterrupt):
                print("Interrupted!", end="", file=sys.stderr)
                sys.stderr.flush()
                _interrupted = True
            else:
                print("Aborted!", end="", file=sys.stderr)
                sys.stderr.flush()
                sys.exit(ExitCode.FAILURE)
        except ClickException as e:
            e.show()
            sys.exit(e.exit_code)
        finally:
            if _interrupted:
                # Override the exit code when it's interrupted,
                # referring https://github.com/python/cpython/pull/11862
                if sys.platform.startswith("win"):
                    # Use STATUS_CONTROL_C_EXIT to notify cmd.exe
                    # for interrupted exit
                    sys.exit(-1073741510)
                else:
                    # Use the default signal handler to set the exit
                    # code properly for interruption.
                    signal.signal(signal.SIGINT, signal.SIG_DFL)
                    os.kill(os.getpid(), signal.SIGINT)


class AliasGroupMixin(click.Group):
    """
    Enable command aliases.

    ref) https://github.com/click-contrib/click-aliases
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands = {}
        self._aliases = {}

    def command(self, *args, **kwargs):
        aliases = kwargs.pop("aliases", [])
        decorator = super().command(*args, **kwargs)
        if not aliases:
            return decorator

        def _decorator(f):
            cmd = decorator(f)
            if aliases:
                self._commands[cmd.name] = aliases
                for alias in aliases:
                    self._aliases[alias] = cmd.name
            return cmd

        return _decorator

    def group(self, *args, **kwargs):
        aliases = kwargs.pop("aliases", [])
        # keep the same class type
        kwargs["cls"] = type(self)
        decorator = super().group(*args, **kwargs)
        if not aliases:
            return decorator

        def _decorator(f):
            cmd = decorator(f)
            if aliases:
                self._commands[cmd.name] = aliases
                for alias in aliases:
                    self._aliases[alias] = cmd.name
            return cmd

        return _decorator

    def get_command(self, ctx, cmd_name):
        if cmd_name in self._aliases:
            cmd_name = self._aliases[cmd_name]
        command = super().get_command(ctx, cmd_name)
        if command:
            return command

    def format_commands(self, ctx, formatter):
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command. Ignore it
            if cmd is None:
                continue
            if cmd.hidden:
                continue
            if subcommand in self._commands:
                aliases = ",".join(sorted(self._commands[subcommand]))
                subcommand = "{0} ({1})".format(subcommand, aliases)
            commands.append((subcommand, cmd))

        # allow for 3 times the default spacing
        if len(commands):
            limit = formatter.width - 6 - max(len(cmd[0]) for cmd in commands)
            rows = []
            for subcommand, cmd in commands:
                help = cmd.get_short_help_str(limit)
                rows.append((subcommand, help))
            if rows:
                with formatter.section("Commands"):
                    formatter.write_dl(rows)


class ExtendedCommandGroup(InterruptAwareCommandMixin, AliasGroupMixin, click.Group):
    pass
