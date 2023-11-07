from __future__ import annotations

import asyncio
import json
import os
import sys
import textwrap
from pathlib import Path
from typing import cast
from weakref import WeakSet

import click
from rich.console import Console
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import (
    ContentSwitcher,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    RichLog,
    Static,
)

from ai.backend.install.utils import shorten_path
from ai.backend.plugin.entrypoint import find_build_root

from . import __version__
from .context import DevContext, PackageContext, current_log
from .types import CliArgs, ConfigError, DistInfo, InstallModes

top_tasks: WeakSet[asyncio.Task] = WeakSet()


class DevSetup(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._task = None

    def compose(self) -> ComposeResult:
        yield Label("Development Setup", classes="mode-title")
        yield RichLog(classes="log")

    async def begin_install(self, dist_info: DistInfo) -> None:
        top_tasks.add(asyncio.create_task(self.install(dist_info)))

    async def install(self, dist_info: DistInfo) -> None:
        _log: RichLog = cast(RichLog, self.query_one(".log"))
        _log_token = current_log.set(_log)
        ctx = DevContext(dist_info, self.app)
        try:
            # prerequisites
            await ctx.check_prerequisites()
            # install
            await ctx.install_halfstack(ha_setup=False)
            await ctx.install()
            # configure
            await ctx.configure()
            await ctx.load_fixtures()
            # post-setup
            await ctx.dump_etcd_config()
        except asyncio.CancelledError:
            _log.write(Text.from_markup("[red]Interrupted!"))
            await asyncio.sleep(1)
            raise
        except Exception as e:
            _log.write(e)
        finally:
            _log.write("")
            _log.write(Text.from_markup("[bright_cyan]All tasks finished. Press q/Q to exit."))
            current_log.reset(_log_token)


class PackageSetup(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._task = None

    def compose(self) -> ComposeResult:
        yield Label("Package Setup", classes="mode-title")
        yield RichLog(classes="log")

    async def begin_install(self, dist_info: DistInfo) -> None:
        top_tasks.add(asyncio.create_task(self.install(dist_info)))

    async def install(self, dist_info: DistInfo) -> None:
        _log: RichLog = cast(RichLog, self.query_one(".log"))
        _log_token = current_log.set(_log)
        ctx = PackageContext(dist_info, self.app)
        try:
            # prerequisites
            if dist_info.target_path.exists():
                # TODO: change to ask overwriting
                raise ConfigError(
                    "The target path {dist_info.target_path} already exists. "
                    "Set '--target-path` option to change it or remove existing directory first."
                )
            await ctx.check_prerequisites()
            # install
            await ctx.install_halfstack(ha_setup=False)
            await ctx.install()
            # configure
            await ctx.configure()
            await ctx.load_fixtures()
            # post-setup
            await ctx.dump_etcd_config()
        except asyncio.CancelledError:
            _log.write(Text.from_markup("[red]Interrupted!"))
            await asyncio.sleep(1)
            raise
        except Exception as e:
            _log.write(e)
        finally:
            _log.write("")
            _log.write(Text.from_markup("[bright_cyan]All tasks finished. Press q/Q to exit."))
            current_log.reset(_log_token)


class ModeMenu(Static):
    """A ListView to choose InstallModes and a description pane underneath."""

    BINDINGS = [
        Binding("left", "cursor_up", show=False),
        Binding("right", "cursor_down", show=False),
    ]

    _dist_info: DistInfo
    _dist_info_path: Path | None

    def __init__(
        self,
        args: CliArgs,
        *,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self._build_root = None
        try:
            self._dist_info_path = Path.cwd() / "DIST-INFO"
            self._dist_info = DistInfo(**json.loads(self._dist_info_path.read_bytes()))
        except FileNotFoundError:
            self._dist_info_path = None
            self._dist_info = DistInfo()
        self._enabled_menus = set()
        self._enabled_menus.add(InstallModes.PACKAGE)
        mode = args.mode
        try:
            self._build_root = find_build_root()
            self._enabled_menus.add(InstallModes.DEVELOP)
            if args.mode is None:
                mode = InstallModes.DEVELOP
        except ValueError:
            if args.mode is None:
                mode = InstallModes.PACKAGE
        if Path("INSTALL-INFO").exists():
            self._enabled_menus.add(InstallModes.MAINTAIN)
        assert mode is not None
        self._mode = mode

    def compose(self) -> ComposeResult:
        yield Label("The installation mode:\n(arrow keys to change, enter to select)")
        if self._dist_info_path is None:
            package_desc = "Install using release packages"
        else:
            package_desc = f"Install using release packages ({shorten_path(self._dist_info_path)})"
        if self._build_root is None:
            develop_desc = "Could not find the source (missing BUILD_ROOT)"
        else:
            develop_desc = (
                f"Install from the current source checkout ({shorten_path(self._build_root)})"
            )
        if InstallModes.MAINTAIN in self._enabled_menus:
            maintain_desc = "Maintain an existing setup"
        else:
            # maintain_desc = "Could not find an existing setup (missing INSTALL-INFO)"
            maintain_desc = "Coming soon!"
        mode_desc: dict[InstallModes, str] = {
            InstallModes.DEVELOP: develop_desc,
            InstallModes.PACKAGE: package_desc,
            InstallModes.MAINTAIN: maintain_desc,
        }
        with ListView(
            id="mode-list", initial_index=list(InstallModes).index(InstallModes(self._mode))
        ) as lv:
            self.lv = lv
            for mode in InstallModes:
                disabled = mode not in self._enabled_menus
                yield ListItem(
                    Vertical(
                        Label(mode, classes="mode-item-title"),
                        Label(mode_desc[mode], classes="mode-item-desc"),
                    ),
                    classes="disabled" if disabled else "",
                    id=f"mode-{mode.value.lower()}",
                )
        yield Label(id="mode-desc")

    def action_cursor_up(self) -> None:
        self.lv.action_cursor_up()

    def action_cursor_down(self) -> None:
        self.lv.action_cursor_down()

    @on(ListView.Selected, "#mode-list", item="#mode-develop")
    def start_develop_mode(self) -> None:
        if InstallModes.DEVELOP not in self._enabled_menus:
            return
        self.app.sub_title = "Development Setup"
        switcher: ContentSwitcher = cast(ContentSwitcher, self.app.query_one("#top"))
        switcher.current = "dev-setup"
        dev_setup: DevSetup = cast(DevSetup, self.app.query_one("#dev-setup"))
        switcher.call_after_refresh(dev_setup.begin_install, self._dist_info)

    @on(ListView.Selected, "#mode-list", item="#mode-package")
    def start_package_mode(self) -> None:
        if InstallModes.PACKAGE not in self._enabled_menus:
            return
        self.app.sub_title = "Package Setup"
        switcher: ContentSwitcher = cast(ContentSwitcher, self.app.query_one("#top"))
        switcher.current = "pkg-setup"
        pkg_setup: PackageSetup = cast(PackageSetup, self.app.query_one("#pkg-setup"))
        switcher.call_after_refresh(pkg_setup.begin_install, self._dist_info)

    @on(ListView.Selected, "#mode-list", item="#mode-maintain")
    def start_maintain_mode(self) -> None:
        if InstallModes.MAINTAIN not in self._enabled_menus:
            return
        pass


class InstallerApp(App):
    BINDINGS = [
        Binding("q", "shutdown", "Quit the installer"),
        Binding("ctrl+c", "shutdown", "Quit the installer", show=False, priority=True),
    ]
    CSS_PATH = "app.tcss"

    def __init__(self, args: CliArgs) -> None:
        super().__init__()
        self._args = args

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        logo_text = textwrap.dedent(r"""
        ____             _                  _      _    ___
        | __ )  __ _  ___| | _____ _ __   __| |    / \  |_ _|
        |  _ \ / _` |/ __| |/ / _ \ '_ \ / _` |   / _ \  | |
        | |_) | (_| | (__|   <  __/ | | | (_| |_ / ___ \ | |
        |____/ \__,_|\___|_|\_\___|_| |_|\__,_(_)_/   \_\___|
        """)
        yield Static(logo_text, id="logo")
        with ContentSwitcher(id="top", initial="mode-menu"):
            yield ModeMenu(self._args, id="mode-menu")
            yield DevSetup(id="dev-setup")
            yield PackageSetup(id="pkg-setup")
        yield Footer()

    def on_mount(self) -> None:
        header: Header = cast(Header, self.query_one("Header"))
        header.tall = True
        self.title = "Backend.AI Installer"

    async def action_shutdown(self, message: str | None = None, exit_code: int = 0) -> None:
        for t in {*top_tasks}:
            if t.done():
                continue
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
        self.exit(return_code=exit_code, message=message)


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
@click.option(
    "--mode",
    type=click.Choice([*InstallModes.__members__], case_sensitive=False),
    default=None,
    help="Override the installation mode. [default: auto-detect]",
)
@click.option(
    "--target-path",
    type=str,
    default=str(Path.home() / "backendai"),
    help="Explicitly set the target installation path. [default: ~/backendai]",
)
# TODO: --show-guide?
@click.version_option(version=__version__)
@click.pass_context
def main(
    cli_ctx: click.Context,
    mode: InstallModes | None,
    target_path: str,
) -> None:
    """The installer"""
    # check sudo permission
    console = Console(stderr=True)
    if os.geteuid() == 0:
        console.print(
            "[bright_red] The script should not be run as root, while it requires"
            " the passwordless sudo privilege."
        )
        sys.exit(1)
    # start installer
    args = CliArgs(mode=mode, target_path=target_path)
    app = InstallerApp(args)
    app.run()
