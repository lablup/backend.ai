from __future__ import annotations

import asyncio
import json
import os
import sys
import textwrap
from pathlib import Path
from weakref import WeakSet

import click
from rich.console import Console
from rich.text import Text
from rich.traceback import Traceback
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Key
from textual.validation import Length
from textual.widgets import (
    Button,
    ContentSwitcher,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Markdown,
    Static,
    TabbedContent,
    TabPane,
)

from ai.backend.install.utils import shorten_path
from ai.backend.install.widgets import InputDialog, SetupLog
from ai.backend.plugin.entrypoint import find_build_root

from . import __version__
from .common import detect_os
from .context import DevContext, PackageContext, current_log
from .types import CliArgs, DistInfo, InstallInfo, InstallModes, InstallVariable, PrerequisiteError

top_tasks: WeakSet[asyncio.Task] = WeakSet()


class DevSetup(Static):
    def __init__(self, *, non_interactive: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self._non_interactive = non_interactive
        self._task = None

    def compose(self) -> ComposeResult:
        yield Label("Development Setup", classes="mode-title")
        with TabbedContent():
            with TabPane("Install Log", id="tab-dev-log"):
                yield SetupLog(wrap=True, classes="log")
            with TabPane("Install Report", id="tab-dev-report"):
                yield Label("Installation is not complete.")

    def begin_install(self, dist_info: DistInfo, install_variable: InstallVariable) -> None:
        self.query_one("SetupLog.log").focus()
        top_tasks.add(asyncio.create_task(self.install(dist_info, install_variable)))

    async def install(self, dist_info: DistInfo, install_variable: InstallVariable) -> None:
        _log = self.query_one(".log", SetupLog)
        _log_token = current_log.set(_log)
        ctx = DevContext(
            dist_info, install_variable, self.app, non_interactive=self._non_interactive
        )
        try:
            # prerequisites
            await ctx.check_prerequisites()
            # install
            await ctx.install()
            # configure
            await ctx.configure()
            # post-setup
            await ctx.populate_images()
            await ctx.dump_install_info()
            install_report = InstallReport(ctx.install_info, id="install-report")
            self.query_one("TabPane#tab-dev-report Label").remove()
            self.query_one("TabPane#tab-dev-report").mount(install_report)
            self.query_one("TabbedContent", TabbedContent).active = "tab-dev-report"
        except asyncio.CancelledError:
            _log.write(Text.from_markup("[red]Interrupted!"))
            await asyncio.sleep(1)
            raise
        except PrerequisiteError as e:
            _log.write(Text.from_markup("[red]:warning: A prerequisite check has failed."))
            _log.write(e)
        except Exception as e:
            _log.write(Text.from_markup("[red]:warning: Unexpected error!"))
            _log.write(e)
            _log.write(Traceback())
        finally:
            _log.write("")
            _log.write(Text.from_markup("[bright_cyan]All tasks finished. Press q/Q to exit."))
            if self._non_interactive:
                self.app.post_message(Key("q", "q"))
            current_log.reset(_log_token)


class PackageSetup(Static):
    def __init__(self, *, non_interactive: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self._non_interactive = non_interactive
        self._task = None

    def compose(self) -> ComposeResult:
        yield Label("Package Setup", classes="mode-title")
        with TabbedContent():
            with TabPane("Install Log", id="tab-pkg-log"):
                yield SetupLog(wrap=True, classes="log")
            with TabPane("Install Report", id="tab-pkg-report"):
                yield Label("Installation is not complete.")

    def begin_install(self, dist_info: DistInfo, install_variable: InstallVariable) -> None:
        self.query_one("SetupLog.log").focus()
        top_tasks.add(asyncio.create_task(self.install(dist_info, install_variable)))

    async def install(self, dist_info: DistInfo, install_variable: InstallVariable) -> None:
        _log = self.query_one(".log", SetupLog)
        _log_token = current_log.set(_log)
        ctx = PackageContext(
            dist_info, install_variable, self.app, non_interactive=self._non_interactive
        )
        try:
            # prerequisites
            if ctx.non_interactive:
                assert dist_info.target_path is not None
            else:
                if dist_info.target_path.exists():
                    input_box = InputDialog(
                        f"The target path {dist_info.target_path} already exists. "
                        "Please set a different target path below, or "
                        "leave the box as blank to overwrite the folder.",
                        str(dist_info.target_path),
                        allow_cancel=False,
                    )
                    _log.mount(input_box)
                    value = await input_box.wait()
                    assert value is not None
                    dist_info.target_path = Path(value)
            await ctx.check_prerequisites()
            # install
            await ctx.install()
            # configure
            await ctx.configure()
            # post-setup
            await ctx.populate_images()
            await ctx.dump_install_info()
            install_report = InstallReport(ctx.install_info, id="install-report")
            self.query_one("TabPane#tab-pkg-report Label").remove()
            self.query_one("TabPane#tab-pkg-report").mount(install_report)
            self.query_one("TabbedContent", TabbedContent).active = "tab-pkg-report"
        except asyncio.CancelledError:
            _log.write(Text.from_markup("[red]Interrupted!"))
            await asyncio.sleep(1)
            raise
        except PrerequisiteError as e:
            _log.write(Text.from_markup("[red]:warning: A prerequisite check has failed."))
            _log.write(e)
        except Exception as e:
            _log.write(Text.from_markup("[red]:warning: Unexpected error!"))
            _log.write(e)
            _log.write(Traceback())
        finally:
            _log.write("")
            _log.write(Text.from_markup("[bright_cyan]All tasks finished. Press q/Q to exit."))
            if self._non_interactive:
                self.app.post_message(Key("q", "q"))
            current_log.reset(_log_token)


class Configure(Static):
    install_variable: InstallVariable | None
    public_facing_address: str | None

    def __init__(self, id: str, **kwargs) -> None:
        super().__init__(**kwargs, id=id)
        self.public_facing_address = None
        self.install_variable = None

    def feed_variables(self, install_variable: InstallVariable) -> None:
        self.install_variable = install_variable
        self.public_facing_address = install_variable.public_facing_address
        address_input = self.app.query_one("#public-ip", Input)
        address_input.value = install_variable.public_facing_address

    def compose(self) -> ComposeResult:
        yield Label("Configure", classes="mode-title")
        with Vertical(id="configure-form"):
            yield Label("Configuration", classes="section-title")
            yield Input(
                placeholder="Public address",
                id="public-ip",
                validate_on=["changed"],
                validators=[Length(minimum=1)],
            )
            with Static(classes="button-group"):
                yield Button("Save", id="save-config", classes="primary")
                yield Button("Cancel", id="cancel-config")

    def close(self) -> None:
        switcher = self.app.query_one("#top", ContentSwitcher)
        switcher.current = "mode-menu"

    @on(Input.Changed, "#public-ip")
    def public_facing_address_changed(self, event: Input.Changed) -> None:
        self.public_facing_address = event.value

    @on(Button.Pressed, "#save-config")
    def save_config(self) -> None:
        assert self.install_variable
        if self.public_facing_address is not None:
            self.install_variable.public_facing_address = self.public_facing_address
        self.close()
        self.app.query_one("#mode-list", ListView).focus()

    @on(Button.Pressed, "#cancel-config")
    def cancel_config(self) -> None:
        self.close()
        self.app.query_one("#mode-list", ListView).focus()


class InstallReport(Static):
    def __init__(self, install_info: InstallInfo, **kwargs) -> None:
        super().__init__(**kwargs)
        self.install_info = install_info

    def compose(self) -> ComposeResult:
        service = self.install_info.service_config
        yield Markdown(
            textwrap.dedent(
                f"""
        Follow each tab's instructions.  Once all 5 service daemons are ready, you may connect to
        `http://{service.webserver_addr.face.host}:{service.webserver_addr.face.port}`.

        Use the following credentials for the admin access:
        - Username: `admin@lablup.com`
        - Password: `wJalrXUt`

        To see this guide again, run './backendai-install-<platform> install --show-guide'.
        """
            )
        )
        with TabbedContent():
            with TabPane("Web Server", id="webserver"):
                yield Markdown(
                    textwrap.dedent(
                        f"""
                Run the following commands in a separate shell:
                ```console
                $ cd {self.install_info.base_path.resolve()}
                $ ./backendai-webserver web start-server
                ```

                It works if the console output ends with something like:
                ```
                ...
                INFO ai.backend.web.server [2215731] serving at {service.webserver_addr.bind.host}:{service.webserver_addr.bind.port}
                INFO ai.backend.web.server [2215731] Using uvloop as the event loop backend
                ```

                To terminate, send SIGINT or press Ctrl+C in the console.
                """
                    )
                )
            with TabPane("Manager", id="manager"):
                yield Markdown(
                    textwrap.dedent(
                        f"""
                Run the following commands in a separate shell:
                ```console
                $ cd {self.install_info.base_path.resolve()}
                $ ./backendai-manager mgr start-server
                ```

                It works if the console output ends with something like:
                ```
                ...
                INFO ai.backend.manager.server [2213274] started handling API requests at {service.manager_addr.bind.host}:{service.manager_addr.bind.port}
                INFO ai.backend.manager.server [2213275] started handling API requests at {service.manager_addr.bind.host}:{service.manager_addr.bind.port}
                INFO ai.backend.manager.server [2213276] started handling API requests at {service.manager_addr.bind.host}:{service.manager_addr.bind.port}
                ```

                To terminate, send SIGINT or press Ctrl+C in the console.
                """
                    )
                )
            with TabPane("Agent", id="agent"):
                yield Markdown(
                    textwrap.dedent(
                        f"""
                Run the following commands in a separate shell:
                ```console
                $ cd {self.install_info.base_path.resolve()}
                $ ./backendai-agent ag start-server
                ```

                It works if the console output ends with something like:
                ```
                ...
                INFO ai.backend.agent.server [2214424] started handling RPC requests at {service.agent_rpc_addr.bind.host}:{service.agent_rpc_addr.bind.port}
                ```

                To terminate, send SIGINT or press Ctrl+C in the console.
                """
                    )
                )
            with TabPane("Storage Proxy", id="storage-proxy"):
                yield Markdown(
                    textwrap.dedent(
                        f"""
                Run the following commands in a separate shell:
                ```console
                $ cd {self.install_info.base_path.resolve()}
                $ ./backendai-storage-proxy storage start-server
                ```

                It works if the console output ends with something like:
                ```
                ...
                INFO ai.backend.storage.server [2216229] Node ID: i-storage-proxy-local
                INFO ai.backend.storage.server [2216229] Using uvloop as the event loop backend
                ```

                To terminate, send SIGINT or press Ctrl+C in the console.
                """
                    )
                )
            with TabPane("Local Proxy", id="wsproxy"):
                yield Markdown(
                    textwrap.dedent(
                        f"""
                Run the following commands in a separate shell:
                ```console
                $ cd {self.install_info.base_path.resolve()}
                $ ./backendai-wsproxy wsproxy start-server
                ```

                It works if the console output ends with something like:
                ```
                ...
                2024-07-03 13:19:44.536 INFO ai.backend.wsproxy.proxy.frontend.http.port [2596460] accepting proxy requests from 0.0.0.0:10200~10300
                2024-07-03 13:19:44.536 INFO ai.backend.wsproxy.server [2596460] started handling API requests at 0.0.0.0:{service.local_proxy_addr.bind.port}
                ...
                ```

                To terminate, send SIGINT or press Ctrl+C in the console.
                """
                    )
                )


class ModeMenu(Static):
    """A ListView to choose InstallModes and a description pane underneath."""

    BINDINGS = [
        Binding("left", "cursor_up", show=False),
        Binding("right", "cursor_down", show=False),
    ]

    _dist_info: DistInfo
    _dist_info_path: Path | None

    install_variable: InstallVariable

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
        self._non_interactive = args.non_interactive
        if args.target_path is not None and args.target_path != str(Path.home() / "backendai"):
            self._dist_info.target_path = Path(args.target_path)
        mode = args.mode
        try:
            self._build_root = find_build_root()
            self._enabled_menus.add(InstallModes.DEVELOP)
            if args.mode is None:
                mode = InstallModes.DEVELOP
        except ValueError:
            if args.mode is None:
                mode = InstallModes.PACKAGE
        # TODO: implement
        # if Path("INSTALL-INFO").exists():
        #     self._enabled_menus.add(InstallModes.MAINTAIN)
        self._enabled_menus.add(InstallModes.CONFIGURE)
        assert mode is not None
        self._mode = mode
        self.install_variable = InstallVariable(public_facing_address=args.public_facing_address)

    def compose(self) -> ComposeResult:
        yield Label(id="heading")
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
        configure_desc = "Configure setup variables before installation."
        mode_desc: dict[InstallModes, str] = {
            InstallModes.DEVELOP: develop_desc,
            InstallModes.PACKAGE: package_desc,
            InstallModes.MAINTAIN: maintain_desc,
            InstallModes.CONFIGURE: configure_desc,
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

    def on_mount(self) -> None:
        self.call_later(self.update_platform_info)
        if self._non_interactive:
            # Trigger the selected mode immediately.
            lv = self.app.query_one("#mode-list", ListView)
            li = self.app.query_one(f"#mode-{self._mode.lower()}", ListItem)
            lv.post_message(ListView.Selected(lv, li))

    async def update_platform_info(self) -> None:
        os_info = await detect_os()
        text = Text()
        text.append("Platform: ")
        text.append_text(os_info.__rich__())  # type: ignore
        text.append("\n\n")
        text.append("Choose the installation mode:\n(arrow keys to change, enter to select)")
        self.query_one("#heading", Static).update(text)

    def action_cursor_up(self) -> None:
        self.lv.action_cursor_up()

    def action_cursor_down(self) -> None:
        self.lv.action_cursor_down()

    @on(ListView.Selected, "#mode-list", item="#mode-develop")
    def start_develop_mode(self) -> None:
        if InstallModes.DEVELOP not in self._enabled_menus:
            return
        self.app.sub_title = "Development Setup"
        switcher = self.app.query_one("#top", ContentSwitcher)
        switcher.current = "dev-setup"
        dev_setup = self.app.query_one("#dev-setup", DevSetup)
        self.app.call_later(dev_setup.begin_install, self._dist_info, self.install_variable)

    @on(ListView.Selected, "#mode-list", item="#mode-package")
    def start_package_mode(self) -> None:
        if InstallModes.PACKAGE not in self._enabled_menus:
            return
        self.app.sub_title = "Package Setup"
        switcher = self.app.query_one("#top", ContentSwitcher)
        switcher.current = "pkg-setup"
        pkg_setup = self.app.query_one("#pkg-setup", PackageSetup)
        self.app.call_later(pkg_setup.begin_install, self._dist_info, self.install_variable)

    @on(ListView.Selected, "#mode-list", item="#mode-maintain")
    def start_maintain_mode(self) -> None:
        if InstallModes.MAINTAIN not in self._enabled_menus:
            return
        pass

    @on(ListView.Selected, "#mode-list", item="#mode-configure")
    def start_configure_mode(self) -> None:
        self.app.sub_title = "Configure Variable"
        switcher = self.app.query_one("#top", ContentSwitcher)
        switcher.current = "configure"
        configure = self.app.query_one("#configure", Configure)
        self.app.call_later(configure.feed_variables, self.install_variable)


class InstallerApp(App):
    BINDINGS = [
        Binding("q", "shutdown", "Interrupt ongoing tasks / Quit the installer"),
        Binding(
            "ctrl+c",
            "shutdown",
            "Interrupt ongoing tasks / Quit the installer",
            show=False,
            priority=True,
        ),
    ]
    CSS_PATH = "app.tcss"

    _args: CliArgs

    def __init__(self, args: CliArgs | None = None) -> None:
        super().__init__()
        if args is None:  # when run as textual dev mode
            args = CliArgs(
                mode=None,
                target_path=str(Path.home() / "backendai"),
                show_guide=False,
                non_interactive=False,
                public_facing_address="127.0.0.1",
            )
        self._args = args

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        logo_text = textwrap.dedent(
            r"""
        __                _                  _      _    ___
        | |__   __ _  ___| | _____ _ __   __| |    / \  |_ _|
        |  _ \ / _` |/ __| |/ / _ \ '_ \ / _` |   / _ \  | |
        | |_) | (_| | (__|   <  __/ | | | (_| |_ / ___ \ | |
        |____/ \__,_|\___|_|\_\___|_| |_|\__,_(_)_/   \_\___|
        """
        )
        yield Static(logo_text, id="logo")
        if self._args.show_guide:
            try:
                install_info = InstallInfo(**json.loads((Path.cwd() / "INSTALL-INFO").read_bytes()))
                yield InstallReport(install_info)
            except IOError as e:
                log = SetupLog()
                log.write("Failed to read INSTALL-INFO!")
                log.write(e)
                yield log
        else:
            with ContentSwitcher(id="top", initial="mode-menu"):
                yield ModeMenu(self._args, id="mode-menu")
                yield DevSetup(id="dev-setup", non_interactive=self._args.non_interactive)
                yield PackageSetup(id="pkg-setup", non_interactive=self._args.non_interactive)
                yield Configure(id="configure")
        yield Footer()

    def on_mount(self) -> None:
        header = self.query_one("Header", Header)
        header.tall = True
        self.title = "Backend.AI Installer"

    async def action_shutdown(self, message: str | None = None, exit_code: int = 0) -> None:
        had_cancelled_tasks = False
        for t in {*top_tasks}:
            if t.done():
                continue
            had_cancelled_tasks = True
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
        if not had_cancelled_tasks:
            # Let the user shutdown twice if there were cancelled tasks,
            # so that the user could inspect what happened.
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
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Run the installer non-interactively from the given CLI options.",
)
@click.option(
    "--target-path",
    type=str,
    default=str(Path.home() / "backendai"),
    help="Explicitly set the target installation path. [default: ~/backendai]",
)
@click.option(
    "--show-guide",
    is_flag=True,
    default=False,
    help="Show the post-install guide using INSTALL-INFO if present.",
)
@click.option(
    "--headless",
    is_flag=True,
    default=False,
    help="Run the installer as headless mode.",
)
@click.option(
    "--public-facing-address",
    type=str,
    default="127.0.0.1",
    help="Set public facing address for the Backend.AI server.",
)
@click.version_option(version=__version__)
@click.pass_context
def main(
    cli_ctx: click.Context,
    mode: InstallModes | None,
    target_path: str,
    show_guide: bool,
    non_interactive: bool,
    headless: bool,
    public_facing_address: str,
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
    args = CliArgs(
        mode=mode,
        target_path=target_path,
        show_guide=show_guide,
        non_interactive=non_interactive,
        public_facing_address=public_facing_address,
    )
    app = InstallerApp(args)
    app.run(headless=headless)
