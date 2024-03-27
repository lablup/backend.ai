from typing import Any, Callable

import click

from ai.backend.common.types import SessionTypes

START_OPTION = [
    click.option(
        "-t",
        "--name",
        "--client-token",
        metavar="NAME",
        type=str,
        default=None,
        help="Specify a human-readable session name. If not set, a random hex string is used.",
    ),
    # job scheduling options
    click.option(
        "--type",
        metavar="SESSTYPE",
        type=click.Choice([*SessionTypes], case_sensitive=False),
        default=SessionTypes.INTERACTIVE,
        help="Either batch or interactive",
    ),
    click.option(
        "--starts-at",
        metavar="STARTS_AT",
        type=str,
        default=None,
        help="Let session to be started at a specific or relative time.",
    ),
    click.option(
        "--enqueue-only",
        is_flag=True,
        help="Enqueue the session and return immediately without waiting for its startup.",
    ),
    click.option(
        "--max-wait",
        metavar="SECONDS",
        type=int,
        default=0,
        help="The maximum duration to wait until the session starts.",
    ),
    click.option(
        "--no-reuse",
        is_flag=True,
        help="Do not reuse existing sessions but return an error.",
    ),
    click.option(
        "--callback-url",
        metavar="CALLBACK_URL",
        type=str,
        default=None,
        help="Callback URL which will be called upon sesison lifecycle events.",
    ),
    # execution environment
    click.option(
        "-e",
        "--env",
        metavar="KEY=VAL",
        type=str,
        multiple=True,
        help="Environment variable (may appear multiple times)",
    ),
    # extra options
    click.option(
        "--tag",
        type=str,
        default=None,
        help="User-defined tag string to annotate sessions.",
    ),
    # resource spec
    click.option(
        "-v",
        "--volume",
        "-m",
        "--mount",
        "mount",
        metavar="NAME[=PATH] or NAME[:PATH]",
        type=str,
        multiple=True,
        help=(
            "User-owned virtual folder names to mount. "
            "If path is not provided, virtual folder will be mounted under /home/work. "
            "When the target path is relative, it is placed under /home/work "
            "with auto-created parent directories if any. "
            "Absolute paths are mounted as-is, but it is prohibited to "
            "override the predefined Linux system directories."
        ),
    ),
    click.option(
        "--scaling-group",
        "--sgroup",
        metavar="SCALING_GROUP",
        type=str,
        default=None,
        help=(
            "The scaling group to execute session. If not specified, "
            "all available scaling groups are included in the scheduling."
        ),
    ),
    click.option(
        "-r",
        "--resources",
        metavar="KEY=VAL",
        type=str,
        multiple=True,
        help=(
            "Set computation resources used by the session "
            "(e.g: -r cpu=2 -r mem=256 -r gpu=1)."
            "1 slot of cpu/gpu represents 1 core. "
            "The unit of mem(ory) is MiB."
        ),
    ),
    click.option(
        "--cluster-size",
        metavar="NUMBER",
        type=int,
        default=1,
        help="The size of cluster in number of containers.",
    ),
    click.option(
        "--resource-opts",
        metavar="KEY=VAL",
        type=str,
        multiple=True,
        help="Resource options for creating compute session (e.g: shmem=64m)",
    ),
    # resource grouping
    click.option(
        "-d",
        "--domain",
        metavar="DOMAIN_NAME",
        default=None,
        help=(
            "Domain name where the session will be spawned. "
            "If not specified, config's domain name will be used."
        ),
    ),
    click.option(
        "-g",
        "--group",
        metavar="GROUP_NAME",
        default=None,
        help=(
            "Group name where the session is spawned. "
            "User should be a member of the group to execute the code."
        ),
    ),
]


def decorator_group(*decs) -> Callable[[Any], Any]:
    def d(f):
        for decorator in decs[::-1]:
            f = decorator(f)
        return f

    return d


def click_start_option() -> Callable[[Any], Any]:
    return decorator_group(
        *START_OPTION,
    )
