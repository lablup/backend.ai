from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import secrets
import subprocess
import sys
from typing import IO, Literal, Sequence
import uuid

import click
from humanize import naturalsize
from tabulate import tabulate

from .main import main
from .pretty import print_wait, print_done, print_error, print_fail, print_info, print_warn
from .ssh import container_ssh_ctx
from .run import format_stats, prepare_env_arg, prepare_resource_arg, prepare_mount_arg
from ..compat import asyncio_run
from ..exceptions import BackendAPIError
from ..session import Session, AsyncSession
from ..types import Undefined, undefined
from .params import CommaSeparatedListType

list_expr = CommaSeparatedListType()


@main.group()
def session():
    """Set of compute session operations"""


def _create_cmd(docs: str = None):

    @click.argument('image')
    @click.option('-t', '--name', '--client-token', metavar='NAME',
                  help='Specify a human-readable session name. '
                       'If not set, a random hex string is used.')
    @click.option('-o', '--owner', '--owner-access-key', metavar='ACCESS_KEY',
                  help='Set the owner of the target session explicitly.')
    # job scheduling options
    @click.option('--type', metavar='SESSTYPE',
                  type=click.Choice(['batch', 'interactive']),
                  default='interactive',
                  help='Either batch or interactive')
    @click.option('--starts-at', metavar='STARTS_AT', type=str, default=None,
                  help='Let session to be started at a specific or relative time.')
    @click.option('-c', '--startup-command', metavar='COMMAND',
                  help='Set the command to execute for batch-type sessions.')
    @click.option('--enqueue-only', is_flag=True,
                  help='Enqueue the session and return immediately without waiting for its startup.')
    @click.option('--max-wait', metavar='SECONDS', type=int, default=0,
                  help='The maximum duration to wait until the session starts.')
    @click.option('--no-reuse', is_flag=True,
                  help='Do not reuse existing sessions but return an error.')
    @click.option('--depends', metavar='SESSION_ID', type=str, multiple=True,
                  help="Set the list of session ID or names that the newly created session depends on. "
                       "The session will get scheduled after all of them successfully finish.")
    @click.option('--callback-url', metavar='CALLBACK_URL', type=str, default=None,
                  help="Callback URL which will be called upon sesison lifecycle events.")
    # execution environment
    @click.option('-e', '--env', metavar='KEY=VAL', type=str, multiple=True,
                  help='Environment variable (may appear multiple times)')
    # extra options
    @click.option('--bootstrap-script', metavar='PATH', type=click.File('r'), default=None,
                  help='A user-defined script to execute on startup.')
    @click.option('--tag', type=str, default=None,
                  help='User-defined tag string to annotate sessions.')
    # resource spec
    @click.option('-v', '--volume', '-m', '--mount', 'mount',
                  metavar='NAME[=PATH]', type=str, multiple=True,
                  help='User-owned virtual folder names to mount. '
                       'If path is not provided, virtual folder will be mounted under /home/work. '
                       'When the target path is relative, it is placed under /home/work '
                       'with auto-created parent directories if any. '
                       'Absolute paths are mounted as-is, but it is prohibited to '
                       'override the predefined Linux system directories.')
    @click.option('--scaling-group', '--sgroup', type=str, default=None,
                  help='The scaling group to execute session. If not specified, '
                       'all available scaling groups are included in the scheduling.')
    @click.option('-r', '--resources', metavar='KEY=VAL', type=str, multiple=True,
                  help='Set computation resources used by the session '
                       '(e.g: -r cpu=2 -r mem=256 -r gpu=1).'
                       '1 slot of cpu/gpu represents 1 core. '
                       'The unit of mem(ory) is MiB.')
    @click.option('--cluster-size', metavar='NUMBER', type=int, default=1,
                  help='The size of cluster in number of containers.')
    @click.option('--cluster-mode', metavar='MODE',
                  type=click.Choice(['single-node', 'multi-node']), default='single-node',
                  help='The mode of clustering.')
    @click.option('--resource-opts', metavar='KEY=VAL', type=str, multiple=True,
                  help='Resource options for creating compute session '
                       '(e.g: shmem=64m)')
    @click.option('--preopen', default=None, type=list_expr,
                  help='Pre-open service ports')
    # resource grouping
    @click.option('-d', '--domain', metavar='DOMAIN_NAME', default=None,
                  help='Domain name where the session will be spawned. '
                       'If not specified, config\'s domain name will be used.')
    @click.option('-g', '--group', metavar='GROUP_NAME', default=None,
                  help='Group name where the session is spawned. '
                       'User should be a member of the group to execute the code.')
    @click.option('--assign-agent', default=None, type=list_expr,
                  help='Show mapping list of tuple which mapped containers with agent. '
                       'When user role is Super Admin. '
                       '(e.g., --assign-agent agent_id_1,agent_id_2,...)')
    def create(
        # base args
        image: str,
        name: str | None,
        owner: str | None,
        # job scheduling options
        type: Literal['batch', 'interactive'],
        starts_at: str | None,
        startup_command: str | None,
        enqueue_only: bool,
        max_wait: bool,
        no_reuse: bool,
        depends: Sequence[str],
        callback_url: str,
        # execution environment
        env: Sequence[str],
        # extra options
        bootstrap_script: IO | None,
        tag: str | None,
        # resource spec
        mount: Sequence[str],
        scaling_group: str | None,
        resources: Sequence[str],
        cluster_size: int,
        cluster_mode: Literal['single-node', 'multi-node'],
        resource_opts: Sequence[str],
        preopen: str | None,
        assign_agent: str | None,
        # resource grouping
        domain: str | None,
        group: str | None,
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
            name = f'pysdk-{secrets.token_hex(5)}'
        else:
            name = name

        ######
        envs = prepare_env_arg(env)
        resources = prepare_resource_arg(resources)
        resource_opts = prepare_resource_arg(resource_opts)
        mount, mount_map = prepare_mount_arg(mount)

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
                    envs=envs,
                    startup_command=startup_command,
                    resources=resources,
                    resource_opts=resource_opts,
                    owner_access_key=owner,
                    domain_name=domain,
                    group_name=group,
                    scaling_group=scaling_group,
                    bootstrap_script=bootstrap_script.read() if bootstrap_script is not None else None,
                    tag=tag,
                    preopen_ports=preopen_ports,
                    assign_agent=assigned_agent_list,
                )
            except Exception as e:
                print_error(e)
                sys.exit(1)
            else:
                if compute_session.status == 'PENDING':
                    print_info('Session ID {0} is enqueued for scheduling.'
                               .format(compute_session.id))
                elif compute_session.status == 'SCHEDULED':
                    print_info('Session ID {0} is scheduled and about to be started.'
                               .format(compute_session.id))
                    return
                elif compute_session.status == 'RUNNING':
                    if compute_session.created:
                        print_info('Session ID {0} is created and ready.'
                                   .format(compute_session.id))
                    else:
                        print_info('Session ID {0} is already running and ready.'
                                   .format(compute_session.id))
                    if compute_session.service_ports:
                        print_info('This session provides the following app services: ' +
                                   ', '.join(sport['name']
                                             for sport in compute_session.service_ports))
                elif compute_session.status == 'TERMINATED':
                    print_warn('Session ID {0} is already terminated.\n'
                               'This may be an error in the compute_session image.'
                               .format(compute_session.id))
                elif compute_session.status == 'TIMEOUT':
                    print_info('Session ID {0} is still on the job queue.'
                               .format(compute_session.id))
                elif compute_session.status in ('ERROR', 'CANCELLED'):
                    print_fail('Session ID {0} has an error during scheduling/startup or cancelled.'
                               .format(compute_session.id))

    if docs is not None:
        create.__doc__ = docs
    return create


main.command(aliases=['start'])(_create_cmd(docs="Alias of \"session create\""))
session.command()(_create_cmd())


def _create_from_template_cmd(docs: str = None):

    @click.argument('template_id')
    @click.option('-t', '--name', '--client-token', metavar='NAME',
                  default=undefined,
                  help='Specify a human-readable session name. '
                       'If not set, a random hex string is used.')
    @click.option('-o', '--owner', '--owner-access-key', metavar='ACCESS_KEY',
                  default=undefined,
                  help='Set the owner of the target session explicitly.')
    # job scheduling options
    @click.option('--type', 'type_', metavar='SESSTYPE',
                  type=click.Choice(['batch', 'interactive', undefined]),  # type: ignore
                  default=undefined,
                  help='Either batch or interactive')
    @click.option('--starts_at', metavar='STARTS_AT', type=str, default=None,
                  help='Let session to be started at a specific or relative time.')
    @click.option('-i', '--image', default=undefined,
                  help='Set compute_session image to run.')
    @click.option('-c', '--startup-command', metavar='COMMAND', default=undefined,
                  help='Set the command to execute for batch-type sessions.')
    @click.option('--enqueue-only', is_flag=True,
                  help='Enqueue the session and return immediately without waiting for its startup.')
    @click.option('--max-wait', metavar='SECONDS', type=int, default=undefined,
                  help='The maximum duration to wait until the session starts.')
    @click.option('--no-reuse', is_flag=True,
                  help='Do not reuse existing sessions but return an error.')
    @click.option('--depends', metavar='SESSION_ID', type=str, multiple=True,
                  help="Set the list of session ID or names that the newly created session depends on. "
                       "The session will get scheduled after all of them successfully finish.")
    @click.option('--callback-url', metavar='CALLBACK_URL', type=str, default=None,
                  help="Callback URL which will be called upon sesison lifecycle events.")
    # execution environment
    @click.option('-e', '--env', metavar='KEY=VAL', type=str, multiple=True,
                  help='Environment variable (may appear multiple times)')
    # extra options
    @click.option('--tag', type=str, default=undefined,
                  help='User-defined tag string to annotate sessions.')
    # resource spec
    @click.option('-m', '--mount', metavar='NAME[=PATH]', type=str, multiple=True,
                  help='User-owned virtual folder names to mount. '
                       'When the target path is relative, it is placed under /home/work '
                       'with auto-created parent directories if any. '
                       'Absolute paths are mounted as-is, but it is prohibited to '
                       'override the predefined Linux system directories.')
    @click.option('--scaling-group', '--sgroup', type=str, default=undefined,
                  help='The scaling group to execute session. If not specified, '
                       'all available scaling groups are included in the scheduling.')
    @click.option('-r', '--resources', metavar='KEY=VAL', type=str, multiple=True,
                  help='Set computation resources used by the session '
                       '(e.g: -r cpu=2 -r mem=256 -r gpu=1).'
                       '1 slot of cpu/gpu represents 1 core. '
                       'The unit of mem(ory) is MiB.')
    @click.option('--cluster-size', metavar='NUMBER', type=int, default=undefined,
                  help='The size of cluster in number of containers.')
    @click.option('--resource-opts', metavar='KEY=VAL', type=str, multiple=True,
                  help='Resource options for creating compute session '
                       '(e.g: shmem=64m)')
    # resource grouping
    @click.option('-d', '--domain', metavar='DOMAIN_NAME', default=None,
                  help='Domain name where the session will be spawned. '
                       'If not specified, config\'s domain name will be used.')
    @click.option('-g', '--group', metavar='GROUP_NAME', default=None,
                  help='Group name where the session is spawned. '
                       'User should be a member of the group to execute the code.')
    # template overrides
    @click.option('--no-mount', is_flag=True,
                  help='If specified, client.py will tell server not to mount '
                       'any vFolders specified at template,')
    @click.option('--no-env', is_flag=True,
                  help='If specified, client.py will tell server not to add '
                       'any environs specified at template,')
    @click.option('--no-resource', is_flag=True,
                  help='If specified, client.py will tell server not to add '
                       'any resource specified at template,')
    def create_from_template(
        # base args
        template_id: str,
        name: str | Undefined,
        owner: str | Undefined,
        # job scheduling options
        type_: Literal['batch', 'interactive'] | Undefined,
        starts_at: str | None,
        image: str | Undefined,
        startup_command: str | Undefined,
        enqueue_only: bool,
        max_wait: int | Undefined,
        no_reuse: bool,
        depends: Sequence[str],
        callback_url: str,
        # execution environment
        env: Sequence[str],
        # extra options
        tag: str | Undefined,
        # resource spec
        mount: Sequence[str],
        scaling_group: str | Undefined,
        resources: Sequence[str],
        cluster_size: int | Undefined,
        resource_opts: Sequence[str],
        # resource grouping
        domain: str | None,
        group: str | None,
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
        IMAGE: The name (and version/platform tags appended after a colon) of session
               runtime or programming language.
        """
        if name is undefined:
            name = f'pysdk-{secrets.token_hex(5)}'
        else:
            name = name

        envs = prepare_env_arg(env) if len(env) > 0 or no_env else undefined
        resources = prepare_resource_arg(resources) if len(resources) > 0 or no_resource else undefined
        resource_opts = (
            prepare_resource_arg(resource_opts)
            if len(resource_opts) > 0 or no_resource else undefined
        )
        prepared_mount, prepared_mount_map = (
            prepare_mount_arg(mount)
            if len(mount) > 0 or no_mount else (undefined, undefined)
        )
        with Session() as session:
            try:
                compute_session = session.ComputeSession.create_from_template(
                    template_id,
                    image=image,
                    name=name,
                    type_=type_,
                    starts_at=starts_at,
                    enqueue_only=enqueue_only,
                    max_wait=max_wait,
                    no_reuse=no_reuse,
                    dependencies=depends,
                    callback_url=callback_url,
                    cluster_size=cluster_size,
                    mounts=prepared_mount,
                    mount_map=prepared_mount_map,
                    envs=envs,
                    startup_command=startup_command,
                    resources=resources,
                    resource_opts=resource_opts,
                    owner_access_key=owner,
                    domain_name=domain,
                    group_name=group,
                    scaling_group=scaling_group,
                    tag=tag,
                )
            except Exception as e:
                print_error(e)
                sys.exit(1)
            else:
                if compute_session.status == 'PENDING':
                    print_info('Session ID {0} is enqueued for scheduling.'
                               .format(name))
                elif compute_session.status == 'SCHEDULED':
                    print_info('Session ID {0} is scheduled and about to be started.'
                               .format(name))
                    return
                elif compute_session.status == 'RUNNING':
                    if compute_session.created:
                        print_info('Session ID {0} is created and ready.'
                                   .format(name))
                    else:
                        print_info('Session ID {0} is already running and ready.'
                                   .format(name))
                    if compute_session.service_ports:
                        print_info('This session provides the following app services: ' +
                                   ', '.join(sport['name']
                                             for sport in compute_session.service_ports))
                elif compute_session.status == 'TERMINATED':
                    print_warn('Session ID {0} is already terminated.\n'
                               'This may be an error in the compute_session image.'
                               .format(name))
                elif compute_session.status == 'TIMEOUT':
                    print_info('Session ID {0} is still on the job queue.'
                               .format(name))
                elif compute_session.status in ('ERROR', 'CANCELLED'):
                    print_fail('Session ID {0} has an error during scheduling/startup or cancelled.'
                               .format(name))

    if docs is not None:
        create_from_template.__doc__ = docs
    return create_from_template


main.command(aliases=['start-from-template'])(
    _create_from_template_cmd(docs="Alias of \"session create-from-template\""),
)
session.command()(_create_from_template_cmd())


def _destroy_cmd(docs: str = None):

    @click.argument('session_names', metavar='SESSID', nargs=-1)
    @click.option('-f', '--forced', is_flag=True,
                  help='Force-terminate the errored sessions (only allowed for admins)')
    @click.option('-o', '--owner', '--owner-access-key', metavar='ACCESS_KEY',
                  help='Specify the owner of the target session explicitly.')
    @click.option('-s', '--stats', is_flag=True,
                  help='Show resource usage statistics after termination')
    def destroy(session_names, forced, owner, stats):
        """
        Terminate and destroy the given session.

        SESSID: session ID given/generated when creating the session.
        """
        if len(session_names) == 0:
            print_warn('Specify at least one session ID. Check usage with "-h" option.')
            sys.exit(1)
        print_wait('Terminating the session(s)...')
        with Session() as session:
            has_failure = False
            for session_name in session_names:
                try:
                    compute_session = session.ComputeSession(session_name, owner)
                    ret = compute_session.destroy(forced=forced)
                except BackendAPIError as e:
                    print_error(e)
                    if e.status == 404:
                        print_info(
                            'If you are an admin, use "-o" / "--owner" option '
                            'to terminate other user\'s session.')
                    has_failure = True
                except Exception as e:
                    print_error(e)
                    has_failure = True
            else:
                if not has_failure:
                    print_done('Done.')
                if stats:
                    stats = ret.get('stats', None) if ret else None
                    if stats:
                        print(format_stats(stats))
                    else:
                        print('Statistics is not available.')
            if has_failure:
                sys.exit(1)

    if docs is not None:
        destroy.__doc__ = docs
    return destroy


main.command(aliases=['rm', 'kill'])(_destroy_cmd(docs="Alias of \"session destroy\""))
session.command(aliases=['rm', 'kill'])(_destroy_cmd())


def _restart_cmd(docs: str = None):

    @click.argument('session_refs', metavar='SESSION_REFS', nargs=-1)
    def restart(session_refs):
        """
        Restart the compute session.

        \b
        SESSION_REF: session ID or name
        """
        if len(session_refs) == 0:
            print_warn('Specify at least one session ID. Check usage with "-h" option.')
            sys.exit(1)
        print_wait('Restarting the session(s)...')
        with Session() as session:
            has_failure = False
            for session_ref in session_refs:
                try:
                    compute_session = session.ComputeSession(session_ref)
                    compute_session.restart()
                except BackendAPIError as e:
                    print_error(e)
                    if e.status == 404:
                        print_info(
                            'If you are an admin, use "-o" / "--owner" option '
                            'to terminate other user\'s session.')
                    has_failure = True
                except Exception as e:
                    print_error(e)
                    has_failure = True
            else:
                if not has_failure:
                    print_done('Done.')
            if has_failure:
                sys.exit(1)

    if docs is not None:
        restart.__doc__ = docs
    return restart


main.command()(_restart_cmd(docs="Alias of \"session restart\""))
session.command()(_restart_cmd())


@session.command()
@click.argument('session_id', metavar='SESSID')
@click.argument('files', type=click.Path(exists=True), nargs=-1)
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
            print_wait('Uploading files...')
            kernel = session.ComputeSession(session_id)
            kernel.upload(files, show_progress=True)
            print_done('Uploaded.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@session.command()
@click.argument('session_id', metavar='SESSID')
@click.argument('files', nargs=-1)
@click.option('--dest', type=Path, default='.',
              help='Destination path to store downloaded file(s)')
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
            print_wait('Downloading file(s) from {}...'
                       .format(session_id))
            kernel = session.ComputeSession(session_id)
            kernel.download(files, dest, show_progress=True)
            print_done('Downloaded to {}.'.format(dest.resolve()))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@session.command()
@click.argument('session_id', metavar='SESSID')
@click.argument('path', metavar='PATH', nargs=1, default='/home/work')
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

            if 'errors' in result and result['errors']:
                print_fail(result['errors'])
                sys.exit(1)

            files = json.loads(result['files'])
            table = []
            headers = ['File name', 'Size', 'Modified', 'Mode']
            for file in files:
                mdt = datetime.fromtimestamp(file['mtime'])
                fsize = naturalsize(file['size'], binary=True)
                mtime = mdt.strftime('%b %d %Y %H:%M:%S')
                row = [file['filename'], fsize, mtime, file['mode']]
                table.append(row)
            print_done('Retrived.')
            print(tabulate(table, headers=headers))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@session.command()
@click.argument('session_id', metavar='SESSID')
def logs(session_id):
    '''
    Shows the full console log of a compute session.

    \b
    SESSID: Session ID or its alias given when creating the session.
    '''
    with Session() as session:
        try:
            print_wait('Retrieving live container logs...')
            kernel = session.ComputeSession(session_id)
            result = kernel.get_logs().get('result')
            logs = result.get('logs') if 'logs' in result else ''
            print(logs)
            print_done('End of logs.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@session.command()
@click.argument('session_id', metavar='SESSID')
@click.argument('new_id', metavar='NEWID')
def rename(session_id, new_id):
    '''
    Renames session name of running session.

    \b
    SESSID: Session ID or its alias given when creating the session.
    NEWID: New Session ID to rename to.
    '''

    with Session() as session:
        try:
            kernel = session.ComputeSession(session_id)
            kernel.rename(new_id)
            print_done(f'Session renamed to {new_id}.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


def _ssh_cmd(docs: str = None):

    @click.argument("session_ref",  type=str, metavar='SESSION_REF')
    @click.option('-p', '--port',  type=int, metavar='PORT', default=9922,
                  help="the port number for localhost")
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
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null",
                        "-o", "NoHostAuthenticationForLocalhost=yes",
                        "-i", key_path,
                        "work@localhost",
                        "-p", str(port),
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
)(_ssh_cmd(docs="Alias of \"session ssh\""))
session.command(
    context_settings=_ssh_cmd_context_settings,
)(_ssh_cmd())


def _scp_cmd(docs: str = None):

    @click.argument("session_ref", type=str, metavar='SESSION_REF')
    @click.argument("src", type=str, metavar='SRC')
    @click.argument("dst", type=str, metavar='DST')
    @click.option('-p', '--port',  type=str, metavar='PORT', default=9922,
                  help="the port number for localhost")
    @click.option('-r',  '--recursive', default=False, is_flag=True,
                  help="recursive flag option to process directories")
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
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null",
                        "-o", "NoHostAuthenticationForLocalhost=yes",
                        "-i", key_path,
                        "-P", str(port),
                        *recursive_args,
                        src, dst,
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
)(_scp_cmd(docs="Alias of \"session scp\""))
session.command(
    context_settings=_ssh_cmd_context_settings,
)(_scp_cmd())


def _events_cmd(docs: str = None):

    @click.argument('session_name_or_id', metavar='SESSION_ID_OR_NAME')
    @click.option('-o', '--owner', '--owner-access-key', 'owner_access_key', metavar='ACCESS_KEY',
                  help='Specify the owner of the target session explicitly.')
    @click.option('--scope', type=click.Choice(['*', 'session', 'kernel']), default='*',
                  help='Filter the events by kernel-specific ones or session-specific ones.')
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
                        print(click.style(ev.event, fg='cyan', bold=True), json.loads(ev.data))

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
main.command()(_events_cmd(docs="Alias of \"session events\""))
session.command()(_events_cmd())
