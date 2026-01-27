from ai.backend.cli.main import main as cli_main
from ai.backend.common.cli import LazyGroup


# Group commands without aliases - lazy loaded
@cli_main.group(cls=LazyGroup, import_name="ai.backend.client.cli.image:image")
def image() -> None:
    """Image commands."""


@cli_main.group(cls=LazyGroup, import_name="ai.backend.client.cli.dotfile:dotfile")
def dotfile() -> None:
    """Provides dotfile operations."""


@cli_main.group(cls=LazyGroup, import_name="ai.backend.client.cli.deployment:deployment")
def deployment() -> None:
    """Set of deployment operations (deployments, revisions, routes)"""


@cli_main.group(cls=LazyGroup, import_name="ai.backend.client.cli.model:model")
def model() -> None:
    """Set of model operations"""


@cli_main.group(cls=LazyGroup, import_name="ai.backend.client.cli.notification:notification")
def notification() -> None:
    """Set of notification operations (channels and rules)"""


@cli_main.group(cls=LazyGroup, import_name="ai.backend.client.cli.server_log:server_logs")
def server_logs() -> None:
    """Provides operations related to server logs."""


@cli_main.group(cls=LazyGroup, import_name="ai.backend.client.cli.service:service")
def service() -> None:
    """Set of service operations"""


@cli_main.group(cls=LazyGroup, import_name="ai.backend.client.cli.network:network")
def network() -> None:
    """Set of inter-container network operations"""


@cli_main.group(
    cls=LazyGroup, import_name="ai.backend.client.cli.scheduling_history:scheduling_history"
)
def scheduling_history() -> None:
    """Scheduling history operations (superadmin only)"""


@cli_main.group(cls=LazyGroup, import_name="ai.backend.client.cli.fair_share:fair_share")
def fair_share() -> None:
    """Fair share scheduler operations (superadmin only)"""


@cli_main.group(cls=LazyGroup, import_name="ai.backend.client.cli.resource_usage:resource_usage")
def resource_usage() -> None:
    """Resource usage history operations (superadmin only)"""


# Groups with aliases in subcommands - still eager load
from . import admin  # noqa  # type: ignore
from . import vfolder  # noqa  # type: ignore
from . import session  # noqa  # type: ignore
from . import session_template  # noqa  # type: ignore

# Non-group modules that register commands directly
from . import config  # noqa  # type: ignore
from . import app, logs, proxy  # noqa  # type: ignore
from . import service_auto_scaling_rule  # noqa  # type: ignore

# extensions is a helper module, not a command module
from . import extensions  # noqa  # type: ignore

# To include the main module as an explicit dependency
from . import main  # noqa
