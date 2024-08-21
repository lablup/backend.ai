from __future__ import annotations

import asyncio
import json
import secrets
import subprocess
import sys
import uuid
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta
from graphlib import TopologicalSorter
from pathlib import Path
from typing import IO, List, Literal, Optional, Sequence

import click
import inquirer
import treelib
from async_timeout import timeout
from dateutil.parser import isoparse
from dateutil.tz import tzutc
from faker import Faker
from humanize import naturalsize
from tabulate import tabulate

from ai.backend.cli.main import main
from ai.backend.cli.params import CommaSeparatedListType, OptionalType
from ai.backend.cli.types import ExitCode, Undefined, undefined
from ai.backend.common.arch import DEFAULT_IMAGE_ARCH
from ai.backend.common.types import ClusterMode

from ...compat import asyncio_run
from ...exceptions import BackendAPIError
from ...func.session import ComputeSession
from ...output.fields import session_fields
from ...output.types import FieldSpec
from ...session import AsyncSession, Session
from .. import events
from ..pretty import (
    ProgressViewer,
    print_done,
    print_error,
    print_fail,
    print_info,
    print_wait,
    print_warn,
)
from .args import click_start_option
from .execute import (
    format_stats,
    prepare_env_arg,
    prepare_mount_arg,
    prepare_resource_arg,
)
from .ssh import container_ssh_ctx

list_expr = CommaSeparatedListType()


@main.group()
def session():
    """Set of compute session operations"""


def _create_cmd(docs: str = None):
    @click.argument("image")
    @click.option(
        "-o",
        "--owner",
        "--owner-access-key",
        metavar="ACCESS_KEY",
        help="Set the owner of the target session explicitly.",
    )
    # job scheduling options
    @click.option(
        "-c",
        "--startup-command",
        metavar="COMMAND",
        help="Set the command to execute for batch-type sessions.",
    )
    @click.option(
        "--depends",
        metavar="SESSION_ID",
        type=str,
        multiple=True,
        help=(
            "Set the list of session ID or names that the newly created session depends on. "
            "The session will get scheduled after all of them successfully finish."
        ),
    )
    # extra options
    @click.option(
        "--bootstrap-script",
        metavar="PATH",
        type=click.File("r"),
        default=None,
        help="A user-defined script to execute on startup.",
    )
    @click.option(
        "--tag", type=str, default=None, help="User-defined tag string to annotate sessions."
    )
    @click.option(
        "--arch",
        "--architecture",
        "architecture",
        metavar="ARCH_NAME",
        type=str,
        default=DEFAULT_IMAGE_ARCH,
        help="Architecture of the image to use.",
    )
    # resource spec
    @click.option(
        "--cluster-mode",
        metavar="MODE",
        type=click.Choice([*ClusterMode], case_sensitive=False),
        default=ClusterMode.SINGLE_NODE,
        help="The mode of clustering.",
    )
    @click.option("--preopen", default=None, type=list_expr, help="Pre-open service ports")
    # resource grouping
    @click.option(
        "--assign-agent",
        default=None,
        type=list_expr,
        help=(
            "Assign the session to specific agents. "
            "This option is only applicable when the user role is Super Admin. "
            "(e.g., --assign-agent agent_id_1,agent_id_2,...)"
        ),
    )
    @click_start_option()
    def create(
        # base args
        image: str,
        name: str | None,  # click_start_option
        owner: str | None,
        # job scheduling options
        type: Literal["batch", "interactive"],  # click_start_option
        starts_at: str | None,  # click_start_option
        startup_command: str | None,
        enqueue_only: bool,  # click_start_option
        max_wait: int,  # click_start_option
        no_reuse: bool,  # click_start_option
        depends: Sequence[str],
        callback_url: str,  # click_start_option
        # execution environment
        env: Sequence[str],  # click_start_option
        # extra options
        bootstrap_script: IO | None,
        tag: str | None,  # click_start_option
        architecture: str,
        # resource spec
        mount: Sequence[str],  # click_start_option
        scaling_group: str | None,  # click_start_option
        resources: Sequence[str],  # click_start_option
        cluster_size: int,  # click_start_option
        cluster_mode: Literal["single-node", "multi-node"],
        resource_opts: Sequence[str],  # click_start_option
        preopen: str | None,
        assign_agent: str | None,
        # resource grouping
        domain: str | None,  # click_start_option
        group: str | None,  # click_start_option
    ) -> None:
        """
        Prepare and start a single compute session without executing codes.
        You may use the created session to execute codes using the "run" command
        or connect to an application service provided by the session using the "app"
        command.


        \b
        IMAGE: The name (and version/platform tags appended after a colon) of session
               runtime or programming language.
        """
        if name is None:
            faker = Faker()
            name = f"pysdk-{faker.user_name()}"
        else:
            name = name

        ######
        envs = prepare_env_arg(env)
        parsed_resources = prepare_resource_arg(resources)
        parsed_resource_opts = prepare_resource_arg(resource_opts)
        mount, mount_map, mount_options = prepare_mount_arg(mount, escape=True)

        preopen_ports = preopen
        assigned_agent_list = assign_agent
        with Session() as session:
            try:
                compute_session = session.ComputeSession.get_or_create(
                    image,
                    name=name,
                    type_=type,
                    starts_at=starts_at,
                    enqueue_only=enqueue_only,
                    max_wait=max_wait,
                    no_reuse=no_reuse,
                    dependencies=depends,
                    callback_url=callback_url,
                    cluster_size=cluster_size,
                    cluster_mode=cluster_mode,
                    mounts=mount,
                    mount_map=mount_map,
                    mount_options=mount_options,
                    envs=envs,
                    startup_command=startup_command,
                    resources=parsed_resources,
                    resource_opts=parsed_resource_opts,
                    owner_access_key=owner,
                    domain_name=domain,
                    group_name=group,
                    scaling_group=scaling_group,
                    bootstrap_script=(
                        bootstrap_script.read() if bootstrap_script is not None else None
                    ),
                    tag=tag,
                    architecture=architecture,
                    preopen_ports=preopen_ports,
                    assign_agent=assigned_agent_list,
                )
            except Exception as e:
                print_error(e)
                sys.exit(ExitCode.FAILURE)
            else:
                if compute_session.status == "PENDING":
                    print_info(
                        "Session ID {0} is enqueued for scheduling.".format(compute_session.id)
                    )
                elif compute_session.status == "SCHEDULED":
                    print_info(
                        "Session ID {0} is scheduled and about to be started.".format(
                            compute_session.id
                        )
                    )
                    return
                elif compute_session.status == "RUNNING":
                    if compute_session.created:
                        print_info(
                            "Session ID {0} is created and ready.".format(compute_session.id)
                        )
                    else:
                        print_info(
                            "Session ID {0} is already running and ready.".format(
                                compute_session.id
                            )
                        )
                    if compute_session.service_ports:
                        print_info(
                            "This session provides the following app services: "
                            + ", ".join(sport["name"] for sport in compute_session.service_ports)
                        )
                elif compute_session.status == "TERMINATED":
                    print_warn(
                        "Session ID {0} is already terminated.\n"
                        "This may be an error in the compute_session image.".format(
                            compute_session.id
                        )
                    )
                elif compute_session.status == "TIMEOUT":
                    print_info(
                        "Session ID {0} is still on the job queue.".format(compute_session.id)
                    )
                elif compute_session.status in ("ERROR", "CANCELLED"):
                    print_fail(
                        "Session ID {0} has an error during scheduling/startup or cancelled.".format(
                            compute_session.id
                        )
                    )

    if docs is not None:
        create.__doc__ = docs
    return create


main.command(aliases=["start"])(_create_cmd(docs='Alias of "session create"'))
session.command()(_create_cmd())


def _create_from_template_cmd(docs: str = None):
    @click.argument("template_id")
    @click_start_option()
    @click.option(
        "-o",
        "--owner",
        "--owner-access-key",
        metavar="ACCESS_KEY",
        type=OptionalType(str),
        default=undefined,
        help="Set the owner of the target session explicitly.",
    )
    # job scheduling options
    @click.option(
        "-i",
        "--image",
        metavar="IMAGE",
        type=OptionalType(str),
        default=undefined,
        help="Set compute_session image to run.",
    )
    @click.option(
        "-c",
        "--startup-command",
        metavar="COMMAND",
        type=OptionalType(str),
        default=undefined,
        help="Set the command to execute for batch-type sessions.",
    )
    @click.option(
        "--depends",
        metavar="SESSION_ID",
        type=str,
        multiple=True,
        help=(
            "Set the list of session ID or names that the newly created session depends on. "
            "The session will get scheduled after all of them successfully finish."
        ),
    )
    # resource spec
    @click.option(
        "--scaling-group",
        "--sgroup",
        metavar="SCALING_GROUP",
        type=OptionalType(str),
        default=undefined,
        help=(
            "The scaling group to execute session. If not specified "
            "all available scaling groups are included in the scheduling."
        ),
    )
    @click.option(
        "--cluster-size",
        metavar="NUMBER",
        type=OptionalType(int),
        default=undefined,
        help="The size of cluster in number of containers.",
    )
    # resource grouping
    @click.option(
        "-d",
        "--domain",
        metavar="DOMAIN_NAME",
        type=OptionalType(str),
        default=undefined,
        help=(
            "Domain name where the session will be spawned. "
            "If not specified, config's domain name will be used."
        ),
    )
    @click.option(
        "-g",
        "--group",
        metavar="GROUP_NAME",
        type=OptionalType(str),
        default=undefined,
        help=(
            "Group name where the session is spawned. "
            "User should be a member of the group to execute the code."
        ),
    )
    # template overrides
    @click.option(
        "--no-mount",
        is_flag=True,
        help=(
            "If specified, client.py will tell server not to mount "
            "any vFolders specified at template,"
        ),
    )
    @click.option(
        "--no-env",
        is_flag=True,
        help=(
            "If specified, client.py will tell server not to add "
            "any environs specified at template,"
        ),
    )
    @click.option(
        "--no-resource",
        is_flag=True,
        help=(
            "If specified, client.py will tell server not to add "
            "any resource specified at template,"
        ),
    )
    def create_from_template(
        # base args
        template_id: str,
        name: str | None,  # click_start_option
        owner: str | Undefined,
        # job scheduling options
        type: Literal["batch", "interactive"],  # click_start_option
        starts_at: str | None,  # click_start_option
        image: str | Undefined,
        startup_command: str | Undefined,
        enqueue_only: bool,  # click_start_option
        max_wait: int,  # click_start_option
        no_reuse: bool,  # click_start_option
        depends: Sequence[str],
        callback_url: str | None,  # click_start_option
        # execution environment
        env: Sequence[str],  # click_start_option
        # extra options
        tag: str | None,  # click_start_option
        # resource spec
        mount: Sequence[str],  # click_start_option
        scaling_group: str | Undefined,
        resources: Sequence[str],  # click_start_option
        cluster_size: int | Undefined,
        resource_opts: Sequence[str],  # click_start_option
        # resource grouping
        domain: str | Undefined,
        group: str | Undefined,
        # template overrides
        no_mount: bool,
        no_env: bool,
        no_resource: bool,
    ) -> None:
        """
        Prepare and start a single compute session without executing codes.
        You may use the created session to execute codes using the "run" command
        or connect to an application service provided by the session using the "app"
        command.

        \b
        TEMPLATE_ID: The template ID to create a session from.
        """
        if name is None:
            name = f"pysdk-{secrets.token_hex(5)}"
        else:
            name = name

        envs = prepare_env_arg(env) if len(env) > 0 or no_env else undefined
        parsed_resources = (
            prepare_resource_arg(resources) if len(resources) > 0 or no_resource else undefined
        )
        parsed_resource_opts = (
            prepare_resource_arg(resource_opts)
            if len(resource_opts) > 0 or no_resource
            else undefined
        )
        prepared_mount, prepared_mount_map, _ = (
            prepare_mount_arg(mount) if len(mount) > 0 or no_mount else (undefined, undefined)
        )
        kwargs = {
            "name": name,
            "type_": type,
            "starts_at": starts_at,
            "enqueue_only": enqueue_only,
            "max_wait": max_wait,
            "no_reuse": no_reuse,
            "dependencies": depends,
            "callback_url": callback_url,
            "cluster_size": cluster_size,
            "mounts": prepared_mount,
            "mount_map": prepared_mount_map,
            "envs": envs,
            "startup_command": startup_command,
            "resources": parsed_resources,
            "resource_opts": parsed_resource_opts,
            "owner_access_key": owner,
            "domain_name": domain,
            "group_name": group,
            "scaling_group": scaling_group,
            "tag": tag,
        }
        kwargs = {key: value for key, value in kwargs.items() if value is not undefined}
        with Session() as session:
            try:
                compute_session = session.ComputeSession.create_from_template(
                    template_id,
                    image=image,
                    **kwargs,
                )
            except Exception as e:
                print_error(e)
                sys.exit(ExitCode.FAILURE)
            else:
                if compute_session.status == "PENDING":
                    print_info("Session ID {0} is enqueued for scheduling.".format(name))
                elif compute_session.status == "SCHEDULED":
                    print_info("Session ID {0} is scheduled and about to be started.".format(name))
                    return
                elif compute_session.status == "RUNNING":
                    if compute_session.created:
                        print_info("Session ID {0} is created and ready.".format(name))
                    else:
                        print_info("Session ID {0} is already running and ready.".format(name))
                    if compute_session.service_ports:
                        print_info(
                            "This session provides the following app services: "
                            + ", ".join(sport["name"] for sport in compute_session.service_ports)
                        )
                elif compute_session.status == "TERMINATED":
                    print_warn(
                        "Session ID {0} is already terminated.\n"
                        "This may be an error in the compute_session image.".format(name)
                    )
                elif compute_session.status == "TIMEOUT":
                    print_info("Session ID {0} is still on the job queue.".format(name))
                elif compute_session.status in ("ERROR", "CANCELLED"):
                    print_fail(
                        "Session ID {0} has an error during scheduling/startup or cancelled.".format(
                            name
                        )
                    )

    if docs is not None:
        create_from_template.__doc__ = docs
    return create_from_template


main.command(aliases=["start-from-template"])(
    _create_from_template_cmd(docs='Alias of "session create-from-template"'),
)
session.command()(_create_from_template_cmd())


def _destroy_cmd(docs: str = None):
    @click.argument("session_names", metavar="SESSID", nargs=-1)
    @click.option(
        "-f",
        "--forced",
        is_flag=True,
        help="Force-terminate the errored sessions (only allowed for admins)",
    )
    @click.option(
        "-o",
        "--owner",
        "--owner-access-key",
        metavar="ACCESS_KEY",
        help="Specify the owner of the target session explicitly.",
    )
    @click.option(
        "-s", "--stats", is_flag=True, help="Show resource usage statistics after termination"
    )
    @click.option(
        "-r", "--recursive", is_flag=True, help="Cancel all the dependant sessions recursively"
    )
    def destroy(session_names, forced, owner, stats, recursive):
        """
        Terminate and destroy the given session.

        SESSID: session ID given/generated when creating the session.
        """
        if len(session_names) == 0:
            print_warn('Specify at least one session ID. Check usage with "-h" option.')
            sys.exit(ExitCode.INVALID_ARGUMENT)
        print_wait("Terminating the session(s)...")
        with Session() as session:
            has_failure = False
            for session_name in session_names:
                try:
                    compute_session = session.ComputeSession(session_name, owner)
                    ret = compute_session.destroy(forced=forced, recursive=recursive)

                except BackendAPIError as e:
                    print_error(e)
                    if e.status == 404:
                        print_info(
                            'If you are an admin, use "-o" / "--owner" option '
                            "to terminate other user's session."
                        )
                    has_failure = True
                except Exception as e:
                    print_error(e)
                    has_failure = True
            else:
                if not has_failure:
                    print_done("Done.")
                    if forced:
                        print_warn(
                            "If you have destroyed a session whose status is one of "
                            "[`PULLING`, `SCHEDULED`, `PREPARING`, `TERMINATING`, `ERROR`], "
                            "Manual cleanup of actual containers may be required."
                        )
                if stats:
                    stats = ret.get("stats", None) if ret else None
                    if stats:
                        print(format_stats(stats))
                    else:
                        print("Statistics is not available.")
            if has_failure:
                sys.exit(ExitCode.FAILURE)

    if docs is not None:
        destroy.__doc__ = docs
    return destroy


main.command(aliases=["rm", "kill"])(_destroy_cmd(docs='Alias of "session destroy"'))
session.command(aliases=["rm", "kill"])(_destroy_cmd())


def _restart_cmd(docs: str = None):
    @click.argument("session_refs", metavar="SESSION_REFS", nargs=-1)
    @click.option(
        "-o",
        "--owner",
        "--owner-access-key",
        metavar="ACCESS_KEY",
        help="Specify the owner of the target session explicitly.",
    )
    def restart(session_refs, owner):
        """
        Restart the compute session.

        \b
        SESSION_REF: session ID or name
        """
        if len(session_refs) == 0:
            print_warn('Specify at least one session ID. Check usage with "-h" option.')
            sys.exit(ExitCode.INVALID_ARGUMENT)
        print_wait("Restarting the session(s)...")
        with Session() as session:
            has_failure = False
            for session_ref in session_refs:
                try:
                    compute_session = session.ComputeSession(session_ref, owner)
                    compute_session.restart()
                except BackendAPIError as e:
                    print_error(e)
                    if e.status == 404:
                        print_info(
                            'If you are an admin, use "-o" / "--owner" option '
                            "to terminate other user's session."
                        )
                    has_failure = True
                except Exception as e:
                    print_error(e)
                    has_failure = True
            else:
                if not has_failure:
                    print_done("Done.")
            if has_failure:
                sys.exit(ExitCode.FAILURE)

    if docs is not None:
        restart.__doc__ = docs
    return restart


main.command()(_restart_cmd(docs='Alias of "session restart"'))
session.command()(_restart_cmd())


@session.command()
@click.argument("session_id", metavar="SESSID")
@click.argument("files", type=click.Path(exists=True), nargs=-1)
def upload(session_id, files):
    """
    Upload the files to a compute session's home directory.
    If the target directory is in a storage folder mount, the operation is
    effectively same to uploading files to the storage folder.
    It is recommended to use storage folder commands for large file transfers
    to utilize the storage proxy.

    For cluster sessions, the files are only uploaded to the main container.

    \b
    SESSID: Session ID or name.
    FILES: One or more paths to upload.
    """
    if len(files) < 1:
        print_warn("Please specify one or more file paths after session ID or name.")
        return
    with Session() as session:
        try:
            print_wait("Uploading files...")
            kernel = session.ComputeSession(session_id)
            kernel.upload(files, show_progress=True)
            print_done("Uploaded.")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@session.command()
@click.argument("session_id", metavar="SESSID")
@click.argument("files", nargs=-1)
@click.option("--dest", type=Path, default=".", help="Destination path to store downloaded file(s)")
def download(session_id, files, dest):
    """
    Download files from a compute session's home directory.
    If the source path is in a storage folder mount, the operation is
    effectively same to downloading files from the storage folder.
    It is recommended to use storage folder commands for large file transfers
    to utilize the storage proxy.

    For cluster sessions, the files are only downloaded from the main container.

    \b
    SESSID: Session ID or name.
    FILES: One or more paths inside compute session.
    """
    if len(files) < 1:
        print_warn("Please specify one or more file paths after session ID or name.")
        return
    with Session() as session:
        try:
            print_wait("Downloading file(s) from {}...".format(session_id))
            kernel = session.ComputeSession(session_id)
            kernel.download(files, dest, show_progress=True)
            print_done("Downloaded to {}.".format(dest.resolve()))
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@session.command()
@click.argument("session_id", metavar="SESSID")
@click.argument("path", metavar="PATH", nargs=1, default="/home/work")
def ls(session_id, path):
    """
    List files in a path of a running compute session.

    For cluster sessions, it lists the files of the main container.

    \b
    SESSID: Session ID or name.
    PATH: Path inside container.
    """
    with Session() as session:
        try:
            print_wait('Retrieving list of files in "{}"...'.format(path))
            kernel = session.ComputeSession(session_id)
            result = kernel.list_files(path)

            if "errors" in result and result["errors"]:
                print_fail(result["errors"])
                sys.exit(ExitCode.FAILURE)

            files = json.loads(result["files"])
            table = []
            headers = ["File name", "Size", "Modified", "Mode"]
            for file in files:
                mdt = datetime.fromtimestamp(file["mtime"])
                fsize = naturalsize(file["size"], binary=True)
                mtime = mdt.strftime("%b %d %Y %H:%M:%S")
                row = [file["filename"], fsize, mtime, file["mode"]]
                table.append(row)
            print_done("Retrived.")
            print(tabulate(table, headers=headers))
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@session.command()
@click.argument("session_id", metavar="SESSID")
@click.option(
    "-k",
    "--kernel",
    "--kernel-id",
    type=str,
    default=None,
    help="The target kernel id of logs. Default value is None, in which case logs of a main kernel are fetched.",
)
def logs(session_id: str, kernel: str | None) -> None:
    """
    Shows the full console log of a compute session.

    \b
    SESSID: Session ID or its alias given when creating the session.
    """
    _kernel_id = uuid.UUID(kernel) if kernel is not None else None
    with Session() as session:
        try:
            print_wait("Retrieving live container logs...")
            _session = session.ComputeSession(session_id)
            result = _session.get_logs(_kernel_id).get("result")
            logs = result.get("logs") if "logs" in result else ""
            print(logs)
            print_done("End of logs.")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@session.command("status-history")
@click.argument("session_id", metavar="SESSID")
def status_history(session_id: str) -> None:
    """
    Shows the status transition history of the compute session.

    \b
    SESSID: Session ID or its alias given when creating the session.
    """
    with Session() as session:
        print_wait("Retrieving status history...")
        kernel = session.ComputeSession(session_id)
        try:
            status_history = kernel.get_status_history().get("result")
            print_info(f"status_history: {status_history}")
            if (preparing := status_history.get("preparing")) is None:
                result = {
                    "result": {
                        "seconds": 0,
                        "microseconds": 0,
                    },
                }
            elif (terminated := status_history.get("terminated")) is None:
                alloc_time_until_now: timedelta = datetime.now(tzutc()) - isoparse(preparing)
                result = {
                    "result": {
                        "seconds": alloc_time_until_now.seconds,
                        "microseconds": alloc_time_until_now.microseconds,
                    },
                }
            else:
                alloc_time: timedelta = isoparse(terminated) - isoparse(preparing)
                result = {
                    "result": {
                        "seconds": alloc_time.seconds,
                        "microseconds": alloc_time.microseconds,
                    },
                }
            print_done(f"Actual Resource Allocation Time: {result}")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@session.command()
@click.argument("session_id", metavar="SESSID")
@click.argument("new_name", metavar="NEWNAME")
def rename(session_id: str, new_name: str) -> None:
    """
    Renames session name of running session.

    \b
    SESSID: Session ID or its alias given when creating the session.
    NEWNAME: New Session name.
    """

    with Session() as session:
        try:
            kernel = session.ComputeSession(session_id)
            kernel.rename(new_name)
            print_done(f"Session renamed to {new_name}.")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@session.command()
@click.argument("session_id", metavar="SESSID")
def commit(session_id: str) -> None:
    """
    Commit a running session to tar file.

    \b
    SESSID: Session ID or its alias given when creating the session.
    """

    with Session() as session:
        try:
            kernel = session.ComputeSession(session_id)
            kernel.commit()
            print_info(f"Request to commit Session(name or id: {session_id})")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@session.command()
@click.argument("session_id", metavar="SESSID_OR_NAME")
@click.argument("image_name", metavar="IMAGENAME")
def convert_to_image(session_id: str, image_name: str) -> None:
    """
    Commits running session to new image and then uploads to designated container registry.
    Requires Backend.AI server set up for per-user image commit feature (24.03).

    \b
    SESSID_OR_NAME: Session ID or its alias given when creating the session.
    IMAGENAME: New image name.
    """

    with Session() as session:
        try:
            _sess = session.ComputeSession(session_id)
            result = _sess.export_to_image(image_name)
            print_info(f"Request to commit Session(name or id: {session_id})")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)

    async def export_tracker(bgtask_id):
        async with AsyncSession() as session:
            try:
                bgtask = session.BackgroundTask(bgtask_id)
                completion_msg_func = lambda: print_done("Session export process completed.")
                async with (
                    bgtask.listen_events() as response,
                    ProgressViewer("Starting the session...") as viewer,
                ):
                    async for ev in response:
                        data = json.loads(ev.data)
                        if ev.event == "bgtask_updated":
                            if viewer.tqdm is None:
                                pbar = await viewer.to_tqdm()

                            pbar = viewer.tqdm
                            pbar.total = data["total_progress"]
                            pbar.update(data["current_progress"] - pbar.n)
                            pbar.display(data["message"])
                        elif ev.event == "bgtask_failed":
                            error_msg = data["message"]
                            completion_msg_func = lambda: print_fail(
                                f"Error during the operation: {error_msg}",
                            )
                        elif ev.event == "bgtask_cancelled":
                            completion_msg_func = lambda: print_warn(
                                "The operation has been cancelled in the middle. "
                                "(This may be due to server shutdown.)",
                            )
            finally:
                completion_msg_func()
                sys.exit()

    asyncio_run(export_tracker(result["task_id"]))


@session.command()
@click.argument("session_id", metavar="SESSID")
def abuse_history(session_id: str) -> None:
    """
    Get abusing reports of session's sibling kernels.

    \b
    SESSID: Session ID or its alias given when creating the session.
    """

    with Session() as api_session:
        try:
            session = api_session.ComputeSession(session_id)
            report = session.get_abusing_report()
            print(report)
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


def _ssh_cmd(docs: str | None = None):
    @click.argument("session_ref", type=str, metavar="SESSION_REF")
    @click.option(
        "-p", "--port", type=int, metavar="PORT", default=9922, help="the port number for localhost"
    )
    @click.pass_context
    def ssh(ctx: click.Context, session_ref: str, port: int) -> None:
        """Execute the ssh command against the target compute session.

        \b
        SESSION_REF: The user-provided name or the unique ID of a running compute session.

        All remaining options and arguments not listed here are passed to the ssh command as-is.
        """
        try:
            with container_ssh_ctx(session_ref, port) as key_path:
                ssh_proc = subprocess.run(
                    [
                        "ssh",
                        "-o",
                        "StrictHostKeyChecking=no",
                        "-o",
                        "UserKnownHostsFile=/dev/null",
                        "-o",
                        "NoHostAuthenticationForLocalhost=yes",
                        "-i",
                        key_path,
                        "work@localhost",
                        "-p",
                        str(port),
                        *ctx.args,
                    ],
                    shell=False,
                    check=False,  # be transparent against the main command
                )
                sys.exit(ssh_proc.returncode)
        except Exception as e:
            print_error(e)

    if docs is not None:
        ssh.__doc__ = docs
    return ssh


_ssh_cmd_context_settings = {
    "ignore_unknown_options": True,
    "allow_extra_args": True,
    "allow_interspersed_args": True,
}

# Make it available as:
# - backend.ai ssh
# - backend.ai session ssh
main.command(
    context_settings=_ssh_cmd_context_settings,
)(_ssh_cmd(docs='Alias of "session ssh"'))
session.command(
    context_settings=_ssh_cmd_context_settings,
)(_ssh_cmd())


def _scp_cmd(docs: str = None):
    @click.argument("session_ref", type=str, metavar="SESSION_REF")
    @click.argument("src", type=str, metavar="SRC")
    @click.argument("dst", type=str, metavar="DST")
    @click.option(
        "-p", "--port", type=str, metavar="PORT", default=9922, help="the port number for localhost"
    )
    @click.option(
        "-r",
        "--recursive",
        default=False,
        is_flag=True,
        help="recursive flag option to process directories",
    )
    @click.pass_context
    def scp(
        ctx: click.Context,
        session_ref: str,
        src: str,
        dst: str,
        port: int,
        recursive: bool,
    ) -> None:
        """
        Execute the scp command against the target compute session.

        \b
        The SRC and DST have the same format with the original scp command,
        either a remote path as "work@localhost:path" or a local path.

        SESSION_REF: The user-provided name or the unique ID of a running compute session.
        SRC: the source path
        DST: the destination path

        All remaining options and arguments not listed here are passed to the ssh command as-is.

        Examples:

        * Uploading a local directory to the session:

          > backend.ai scp mysess -p 9922 -r tmp/ work@localhost:tmp2/

        * Downloading a directory from the session:

          > backend.ai scp mysess -p 9922 -r work@localhost:tmp2/ tmp/
        """
        recursive_args = []
        if recursive:
            recursive_args.append("-r")
        try:
            with container_ssh_ctx(session_ref, port) as key_path:
                scp_proc = subprocess.run(
                    [
                        "scp",
                        "-o",
                        "StrictHostKeyChecking=no",
                        "-o",
                        "UserKnownHostsFile=/dev/null",
                        "-o",
                        "NoHostAuthenticationForLocalhost=yes",
                        "-i",
                        key_path,
                        "-P",
                        str(port),
                        *recursive_args,
                        src,
                        dst,
                        *ctx.args,
                    ],
                    shell=False,
                    check=False,  # be transparent against the main command
                )
                sys.exit(scp_proc.returncode)
        except Exception as e:
            print_error(e)

    if docs is not None:
        scp.__doc__ = docs
    return scp


# Make it available as:
# - backend.ai scp
# - backend.ai session scp
main.command(
    context_settings=_ssh_cmd_context_settings,
)(_scp_cmd(docs='Alias of "session scp"'))
session.command(
    context_settings=_ssh_cmd_context_settings,
)(_scp_cmd())


def _events_cmd(docs: str = None):
    @click.argument("session_name_or_id", metavar="SESSION_ID_OR_NAME")
    @click.option(
        "-o",
        "--owner",
        "--owner-access-key",
        "owner_access_key",
        metavar="ACCESS_KEY",
        help="Specify the owner of the target session explicitly.",
    )
    @click.option(
        "--scope",
        type=click.Choice(["*", "session", "kernel"]),
        default="*",
        help="Filter the events by kernel-specific ones or session-specific ones.",
    )
    def events(session_name_or_id, owner_access_key, scope):
        """
        Monitor the lifecycle events of a compute session.

        SESSID: session ID or its alias given when creating the session.
        """

        async def _run_events():
            async with AsyncSession() as session:
                try:
                    session_id = uuid.UUID(session_name_or_id)
                    compute_session = session.ComputeSession.from_session_id(session_id)
                except ValueError:
                    compute_session = session.ComputeSession(session_name_or_id, owner_access_key)
                async with compute_session.listen_events(scope=scope) as response:
                    async for ev in response:
                        click.echo(
                            click.style(ev.event, fg="cyan", bold=True)
                            + " "
                            + json.dumps(json.loads(ev.data), indent=None)  # as single-line
                        )

        try:
            asyncio_run(_run_events())
        except Exception as e:
            print_error(e)

    if docs is not None:
        events.__doc__ = docs
    return events


# Make it available as:
# - backend.ai events
# - backend.ai session events
main.command()(_events_cmd(docs='Alias of "session events"'))
session.command()(_events_cmd())


def _fetch_session_names() -> tuple[str]:
    status = ",".join([
        "PENDING",
        "SCHEDULED",
        "PREPARING",
        "RUNNING",
        "RUNNING_DEGRADED",
        "RESTARTING",
        "TERMINATING",
        "ERROR",
    ])
    fields: List[FieldSpec] = [
        session_fields["name"],
        session_fields["session_id"],
        session_fields["group_name"],
        session_fields["main_kernel_id"],
        session_fields["image"],
        session_fields["type"],
        session_fields["status"],
        session_fields["status_info"],
        session_fields["status_changed"],
        session_fields["result"],
    ]
    with Session() as api_session:
        sessions = api_session.ComputeSession.paginated_list(
            status=status,
            access_key=None,
            fields=fields,
            page_offset=0,
            page_size=10,
            filter=None,
            order=None,
        )
    return tuple(map(lambda x: x.get("name"), sessions.items))


def _watch_cmd(docs: Optional[str] = None):
    @click.argument("session_name_or_id", metavar="SESSION_ID_OR_NAME", nargs=-1)
    @click.option(
        "-o",
        "--owner",
        "--owner-access-key",
        "owner_access_key",
        metavar="ACCESS_KEY",
        help="Specify the owner of the target session explicitly.",
    )
    @click.option(
        "--scope",
        type=click.Choice(["*", "session", "kernel"]),
        default="*",
        help="Filter the events by kernel-specific ones or session-specific ones.",
    )
    @click.option(
        "--max-wait",
        metavar="SECONDS",
        type=int,
        default=0,
        help="The maximum duration to wait until the session starts.",
    )
    @click.option(
        "--output",
        type=click.Choice(["json", "console"]),
        default="console",
        help="Set the output style of the command results.",
    )
    def watch(
        session_name_or_id: str, owner_access_key: str, scope: str, max_wait: int, output: str
    ):
        """
        Monitor the lifecycle events of a compute session
        and display in human-friendly interface.
        """
        session_names = _fetch_session_names()
        if not session_names:
            if output == "json":
                sys.stderr.write(f'{json.dumps({"ok": False, "reason": "No matching items."})}\n')
            else:
                print_fail("No matching items.")
            sys.exit(ExitCode.FAILURE)

        if not session_name_or_id:
            questions = [
                inquirer.List(
                    "session",
                    message="Select session to watch.",
                    choices=session_names,
                )
            ]
            session_name_or_id = inquirer.prompt(questions).get("session")
        else:
            for session_name in session_names:
                if session_name.startswith(session_name_or_id[0]):
                    session_name_or_id = session_name
                    break
            else:
                if output == "json":
                    sys.stderr.write(
                        f'{json.dumps({"ok": False, "reason": "No matching items."})}\n'
                    )
                else:
                    print_fail("No matching items.")
                sys.exit(ExitCode.FAILURE)

        async def handle_console_output(
            session: ComputeSession, scope: Literal["*", "session", "kernel"] = "*"
        ):
            async with session.listen_events(scope=scope) as response:  # AsyncSession
                async for ev in response:
                    match ev.event:
                        case events.SESSION_SUCCESS:
                            print_done(events.SESSION_SUCCESS)
                            sys.exit(json.loads(ev.data).get("exitCode", 0))
                        case events.SESSION_FAILURE:
                            print_fail(events.SESSION_FAILURE)
                            sys.exit(json.loads(ev.data).get("exitCode", 1))
                        case events.KERNEL_CANCELLED:
                            print_fail(events.KERNEL_CANCELLED)
                            break
                        case events.SESSION_TERMINATED:
                            print_done(events.SESSION_TERMINATED)
                            break
                        case _:
                            print_done(ev.event)

        async def handle_json_output(
            session: ComputeSession, scope: Literal["*", "session", "kernel"] = "*"
        ):
            async with session.listen_events(scope=scope) as response:  # AsyncSession
                async for ev in response:
                    event = json.loads(ev.data)
                    event["event"] = ev.event
                    click.echo(event)

                    match ev.event:
                        case events.SESSION_SUCCESS:
                            sys.exit(event.get("exitCode", 0))
                        case events.SESSION_FAILURE:
                            sys.exit(event.get("exitCode", 1))
                        case events.SESSION_TERMINATED | events.KERNEL_CANCELLED:
                            break

        async def _run_events():
            async with AsyncSession() as session:
                try:
                    session_id = uuid.UUID(session_name_or_id)
                    compute_session = session.ComputeSession.from_session_id(session_id)
                except ValueError:
                    compute_session = session.ComputeSession(session_name_or_id, owner_access_key)

                if output == "console":
                    await handle_console_output(session=compute_session, scope=scope)
                elif output == "json":
                    await handle_json_output(session=compute_session, scope=scope)

        async def _run_events_with_timeout(max_wait: int):
            try:
                async with timeout(max_wait):
                    await _run_events()
            except asyncio.TimeoutError:
                sys.exit(ExitCode.OPERATION_TIMEOUT)

        try:
            if max_wait > 0:
                asyncio_run(_run_events_with_timeout(max_wait))
            else:
                asyncio_run(_run_events())
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)

    if docs is not None:
        watch.__doc__ = docs
    return watch


def get_dependency_session_table(root_node: OrderedDict) -> List[OrderedDict]:
    ts: TopologicalSorter = TopologicalSorter()
    session_info_dict = {}
    visited = {}

    def construct_topological_sorter(session: OrderedDict):
        visited[session["session_id"]] = True
        session_info_dict[session["session_id"]] = session
        ts.add(
            session["session_id"],
            *map(lambda session: session["session_id"], session["depends_on"]),
        )

        for dependency_session in session["depends_on"]:
            if not visited.get(dependency_session["session_id"]):
                construct_topological_sorter(dependency_session)

    construct_topological_sorter(root_node)
    return [*map(lambda session_id: session_info_dict[session_id], [*ts.static_order()])]


def show_dependency_session_table(root_node: OrderedDict) -> None:
    table = get_dependency_session_table(root_node)
    header_keys = ["session_name", "session_id", "status", "status_changed"]

    print(
        tabulate(
            [
                header_keys,
                *map(
                    lambda item: [
                        *map(lambda key: item[key], header_keys),
                    ],
                    table,
                ),
            ],
            headers="firstrow",
        )
    )


def get_dependency_session_tree(root_node: OrderedDict) -> treelib.Tree:
    dependency_tree = treelib.Tree()

    root_session_name = root_node["session_name"]
    session_name_counter: defaultdict = defaultdict(lambda: 1)
    session_name_counter[root_session_name] += 1

    def discard_below_dot(time_str: str) -> str:
        return time_str.split(".")[0]

    def get_node_name(session: OrderedDict) -> str:
        task_name = session["session_name"].split("-")[-2]
        status = session["status"].split("KernelStatus.")[1]
        delta = ""

        if session["status_changed"] != "None":
            status_changed = datetime.strptime(
                discard_below_dot(session["status_changed"]), "%Y-%m-%d %H:%M:%S"
            )
            delta = f" {discard_below_dot(str(datetime.now() - status_changed))} ago"

        return f'{task_name} ("{status}"{delta})'

    def get_node_id(session_name: str) -> str:
        return "@".join([session_name, str(session_name_counter[session_name])])

    dependency_tree.create_node(get_node_name(root_node), get_node_id(root_session_name))

    def construct_dependency_tree(session_name: str, dependency_sessions: OrderedDict) -> None:
        for dependency_session in dependency_sessions:
            dependency_session_name = dependency_session["session_name"]
            session_name_counter[dependency_session_name] += 1

            dependency_tree.create_node(
                get_node_name(dependency_session),
                get_node_id(dependency_session_name),
                parent=get_node_id(session_name),
            )

            construct_dependency_tree(dependency_session_name, dependency_session["depends_on"])

    construct_dependency_tree(root_node["session_name"], root_node["depends_on"])
    return dependency_tree


@session.command("show-graph")
@click.argument("session_id", metavar="SESSID")
@click.option("--table", "-t", is_flag=True, help="Show the dependency graph as a form of table.")
def show_dependency_graph(session_id: uuid.UUID | str, table: bool):
    """
    Shows the dependency graph of a compute session.
    \b
    SESSID: Session ID or its alias given when creating the session.
    """

    with Session() as session:
        print_wait("Retrieving the session dependencies graph...")
        print()

        kernel = session.ComputeSession(str(session_id))

        if table:
            show_dependency_session_table(kernel.get_dependency_graph())
        else:
            get_dependency_session_tree(kernel.get_dependency_graph()).show()

        print_done("End of session dependencies graph.")


# Make it available as:
# - backend.ai watch
# - backend.ai session watch
main.command()(_watch_cmd(docs='Alias of "session watch"'))
session.command()(_watch_cmd())
