from __future__ import annotations

import asyncio
from typing import cast
from weakref import WeakSet

import click
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
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

from ai.backend.install import __version__
from ai.backend.plugin.entrypoint import find_build_root

from .types import InstallModes

top_tasks: WeakSet[asyncio.Task] = WeakSet()


class DevSetup(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._task = None

    def compose(self) -> ComposeResult:
        yield Label("Development Setup", classes="mode-title")
        yield RichLog(classes="log")

    async def begin_install(self) -> None:
        top_tasks.add(asyncio.create_task(self.install()))

    async def install(self) -> None:
        log: RichLog = cast(RichLog, self.query_one(".log"))
        try:
            for tick in range(3):
                await asyncio.sleep(1)
                log.write(Text.from_markup(f"[gold1](dev)[/] something is going: {tick}"))
        except asyncio.CancelledError:
            log.write(Text.from_markup("[red]Interrupted!"))
            await asyncio.sleep(1)
            raise


class PackageSetup(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._task = None

    def compose(self) -> ComposeResult:
        yield Label("Package Setup", classes="mode-title")
        yield RichLog(classes="log")

    async def begin_install(self) -> None:
        top_tasks.add(asyncio.create_task(self.install()))

    async def install(self) -> None:
        log: RichLog = cast(RichLog, self.query_one(".log"))
        try:
            for tick in range(3):
                await asyncio.sleep(1)
                log.write(Text.from_markup(f"[gold1](pkg)[/] something is going: {tick}"))
        except asyncio.CancelledError:
            log.write(Text.from_markup("[red]Interrupted!"))
            await asyncio.sleep(1)
            raise


class ModeMenu(Static):
    """A ListView to choose InstallModes and a description pane underneath."""

    def __init__(
        self,
        mode: InstallModes | None = None,
        *,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self._build_root = None
        if mode is None:
            try:
                self._build_root = find_build_root()
                self._dev_available = True
                mode = InstallModes.DEV
            except ValueError:
                self._dev_available = False
                mode = InstallModes.PACKAGE
        assert mode is not None
        self._mode = mode

    def compose(self) -> ComposeResult:
        yield Label("The installation mode:\n(up/down to change, enter to select)")
        mode_desc: dict[tuple[InstallModes, bool], str] = {
            (
                InstallModes.DEV,
                False,
            ): f"Install for development using the current source checkout ({self._build_root})",
            (
                InstallModes.DEV,
                True,
            ): "Could not find the source clone as no BUILD_ROOT file is detected.",
            (InstallModes.PACKAGE, False): "Install using release packages",
        }
        with ListView(
            id="mode-list", initial_index=list(InstallModes).index(InstallModes(self._mode))
        ):
            for mode in InstallModes:
                disabled = not self._dev_available if mode == InstallModes.DEV else False
                yield ListItem(
                    Horizontal(
                        Label(mode, classes="mode-item-title"),
                        Label(mode_desc[(mode, disabled)], classes="mode-item-desc"),
                    ),
                    classes="disabled" if disabled else "",
                    id=f"mode-{mode.value.lower()}",
                )
        yield Label(id="mode-desc")

    @on(ListView.Selected, "#mode-list", item="#mode-dev")
    def start_dev_mode(self) -> None:
        if not self._dev_available:
            return
        self.app.sub_title = "Development Setup"
        switcher: ContentSwitcher = cast(ContentSwitcher, self.app.query_one("#top"))
        switcher.current = "dev-setup"
        dev_setup: DevSetup = cast(DevSetup, self.app.query_one("#dev-setup"))
        switcher.call_after_refresh(dev_setup.begin_install)

    @on(ListView.Selected, "#mode-list", item="#mode-package")
    def start_package_mode(self) -> None:
        self.app.sub_title = "Package Setup"
        switcher: ContentSwitcher = cast(ContentSwitcher, self.app.query_one("#top"))
        switcher.current = "pkg-setup"
        pkg_setup: PackageSetup = cast(PackageSetup, self.app.query_one("#pkg-setup"))
        switcher.call_after_refresh(pkg_setup.begin_install)


class InstallerApp(App):
    BINDINGS = [
        Binding("q", "quit", "Quit the installer"),
        Binding("ctrl+c", "quit", "Quit the installer", show=False, priority=True),
    ]
    CSS_PATH = "app.tcss"

    def __init__(self, mode: InstallModes | None = None) -> None:
        super().__init__()
        self._mode = mode

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with ContentSwitcher(id="top", initial="mode-menu"):
            yield ModeMenu(self._mode, id="mode-menu")
            yield DevSetup(id="dev-setup")
            yield PackageSetup(id="pkg-setup")
        yield Footer()

    def on_mount(self) -> None:
        header: Header = cast(Header, self.query_one("Header"))
        header.tall = True
        self.title = "Backend.AI Installer"

    async def action_quit(self):
        for t in {*top_tasks}:
            if t.done():
                continue
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
        self.exit()


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
@click.version_option(version=__version__)
@click.pass_context
def main(
    ctx: click.Context,
    mode: InstallModes | None,
) -> None:
    """The installer"""
    app = InstallerApp(mode)
    app.run()
