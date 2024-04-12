import asyncio
import collections
import getpass
import itertools
import json
import secrets
import string
import sys
import traceback
from decimal import Decimal
from typing import Mapping, Optional, Sequence, Tuple

import aiohttp
import click
import tabulate as tabulate_mod
from humanize import naturalsize
from tabulate import tabulate

from ai.backend.cli.main import main
from ai.backend.cli.params import CommaSeparatedListType, RangeExprOptionType
from ai.backend.cli.types import ExitCode
from ai.backend.common.arch import DEFAULT_IMAGE_ARCH
from ai.backend.common.types import ClusterMode, MountExpression

from ...compat import asyncio_run, current_loop
from ...config import local_cache_path
from ...exceptions import BackendError
from ...session import AsyncSession
from ..pretty import (
    format_info,
    print_done,
    print_error,
    print_fail,
    print_info,
    print_wait,
    print_warn,
)
from .args import click_start_option

tabulate_mod.PRESERVE_WHITESPACE = True
range_expr = RangeExprOptionType()
list_expr = CommaSeparatedListType()


async def exec_loop(
    stdout,
    stderr,
    compute_session,
    mode,
    code,
    *,
    opts=None,
    vprint_done=print_done,
    is_multi=False,
):
    """
    Fully streamed asynchronous version of the execute loop.
    """
    async with compute_session.stream_execute(code, mode=mode, opts=opts) as stream:
        async for result in stream:
            if result.type == aiohttp.WSMsgType.TEXT:
                result = json.loads(result.data)
            else:
                # future extension
                continue
            for rec in result.get("console", []):
                if rec[0] == "stdout":
                    print(rec[1], end="", file=stdout)
                elif rec[0] == "stderr":
                    print(rec[1], end="", file=stderr)
                else:
                    print("----- output record (type: {0}) -----".format(rec[0]), file=stdout)
                    print(rec[1], file=stdout)
                    print("----- end of record -----", file=stdout)
            stdout.flush()
            files = result.get("files", [])
            if files:
                print("--- generated files ---", file=stdout)
                for item in files:
                    print("{0}: {1}".format(item["name"], item["url"]), file=stdout)
                print("--- end of generated files ---", file=stdout)
            if result["status"] == "clean-finished":
                exitCode = result.get("exitCode")
                msg = "Clean finished. (exit code = {0})".format(exitCode)
                if is_multi:
                    print(msg, file=stderr)
                vprint_done(msg)
            elif result["status"] == "build-finished":
                exitCode = result.get("exitCode")
                msg = "Build finished. (exit code = {0})".format(exitCode)
                if is_multi:
                    print(msg, file=stderr)
                vprint_done(msg)
            elif result["status"] == "finished":
                exitCode = result.get("exitCode")
                msg = "Execution finished. (exit code = {0})".format(exitCode)
                if is_multi:
                    print(msg, file=stderr)
                vprint_done(msg)
                break
            elif result["status"] == "waiting-input":
                if result["options"].get("is_password", False):
                    code = getpass.getpass()
                else:
                    code = input()
                await stream.send_str(code)
            elif result["status"] == "continued":
                pass


def exec_loop_sync(
    stdout, stderr, compute_session, mode, code, *, opts=None, vprint_done=print_done
):
    """
    Old synchronous polling version of the execute loop.
    """
    opts = opts if opts else {}
    run_id = None  # use server-assigned run ID
    while True:
        result = compute_session.execute(run_id, code, mode=mode, opts=opts)
        run_id = result["runId"]
        opts.clear()  # used only once
        for rec in result["console"]:
            if rec[0] == "stdout":
                print(rec[1], end="", file=stdout)
            elif rec[0] == "stderr":
                print(rec[1], end="", file=stderr)
            else:
                print("----- output record (type: {0}) -----".format(rec[0]), file=stdout)
                print(rec[1], file=stdout)
                print("----- end of record -----", file=stdout)
        stdout.flush()
        files = result.get("files", [])
        if files:
            print("--- generated files ---", file=stdout)
            for item in files:
                print("{0}: {1}".format(item["name"], item["url"]), file=stdout)
            print("--- end of generated files ---", file=stdout)
        if result["status"] == "clean-finished":
            exitCode = result.get("exitCode")
            vprint_done("Clean finished. (exit code = {0}".format(exitCode), file=stdout)
            mode = "continue"
            code = ""
        elif result["status"] == "build-finished":
            exitCode = result.get("exitCode")
            vprint_done("Build finished. (exit code = {0})".format(exitCode), file=stdout)
            mode = "continue"
            code = ""
        elif result["status"] == "finished":
            exitCode = result.get("exitCode")
            vprint_done("Execution finished. (exit code = {0})".format(exitCode), file=stdout)
            break
        elif result["status"] == "waiting-input":
            mode = "input"
            if result["options"].get("is_password", False):
                code = getpass.getpass()
            else:
                code = input()
        elif result["status"] == "continued":
            mode = "continue"
            code = ""


async def exec_terminal(compute_session, *, vprint_wait=print_wait, vprint_done=print_done):
    # async with compute_session.stream_pty() as stream: ...
    raise NotImplementedError


def _noop(*args, **kwargs):
    pass


def format_stats(stats):
    formatted = []
    version = stats.pop("version", 1)
    stats.pop("status")
    if version == 1:
        stats.pop("precpu_used", None)
        stats.pop("precpu_system_used", None)
        stats.pop("cpu_system_used", None)
        for key, val in stats.items():
            if key.endswith("_size") or key.endswith("_bytes"):
                val = naturalsize(val, binary=True)
            elif key == "cpu_used":
                key += "_msec"
                val = "{0:,}".format(int(val))
            else:
                val = "{0:,}".format(int(val))
            formatted.append((key, val))
    elif version == 2:
        max_integer_len = 0
        max_fraction_len = 0
        for key, metric in stats.items():
            unit = metric["unit_hint"]
            match unit:
                case "bytes":
                    val = metric.get("stats.max", metric["current"])
                    val = naturalsize(val, binary=True)
                    val, unit = val.rsplit(" ", maxsplit=1)
                    val = "{:,}".format(Decimal(val))
                case "msec" | "usec" | "sec":
                    val = "{:,}".format(Decimal(metric["current"]))
                case "percent" | "pct" | "%":
                    val = metric["pct"]
                    unit = "%"
                case _:
                    val = metric["current"]
                    unit = ""
            if val is None:
                continue
            ip, _, fp = val.partition(".")
            max_integer_len = max(len(ip), max_integer_len)
            max_fraction_len = max(len(fp), max_fraction_len)
            formatted.append([key, val, unit])
        fstr_int_only = "{0:>" + str(max_integer_len) + "}"
        fstr_float = "{0:>" + str(max_integer_len) + "}.{1:<" + str(max_fraction_len) + "}"
        for item in formatted:
            ip, _, fp = item[1].partition(".")
            if fp == "":
                item[1] = fstr_int_only.format(ip) + " " * (max_fraction_len + 1)
            else:
                item[1] = fstr_float.format(ip, fp)
    else:
        print_warn("Unsupported statistics result version. Upgrade your client.")
    return tabulate(formatted)


def prepare_resource_arg(resources: Sequence[str]) -> Mapping[str, str]:
    if resources:
        parsed = {k: v for k, v in map(lambda s: s.split("=", 1), resources)}
        if (mem_arg := parsed.get("mem")) is not None and not mem_arg[-1].isalpha():
            # The default suffix is "m" (mega) if not specified.
            parsed["mem"] = f"{mem_arg}m"
    else:
        parsed = {}  # use the defaults configured in the server
    return parsed


def prepare_env_arg(env: Sequence[str]) -> Mapping[str, str]:
    if env is not None:
        envs = {k: v for k, v in map(lambda s: s.split("=", 1), env)}
    else:
        envs = {}
    return envs


def prepare_mount_arg(
    mount_args: Optional[Sequence[str]] = None,
    *,
    escape: bool = True,
) -> Tuple[Sequence[str], Mapping[str, str], Mapping[str, Mapping[str, str]]]:
    """
    Parse the list of mount arguments into a list of
    vfolder name and in-container mount path pairs,
    followed by extra options.

    :param mount_args: A list of mount arguments such as
        [
            "type=bind,source=/colon:path/test,target=/data",
            "type=bind,source=/colon:path/abcd,target=/zxcv,readonly",
            # simple formats are still supported
            "vf-abcd:/home/work/zxcv",
        ]
    """
    mounts = set()
    mount_map = {}
    mount_options = {}
    if mount_args is not None:
        for mount_arg in mount_args:
            mountpoint = {**MountExpression(mount_arg).parse(escape=escape)}
            mount = str(mountpoint.pop("source"))
            mounts.add(mount)
            if target := mountpoint.pop("target", None):
                mount_map[mount] = str(target)
            mount_options[mount] = mountpoint
    return list(mounts), mount_map, mount_options


@main.command()
@click.argument("image", type=str)
@click.argument("files", nargs=-1, type=click.Path())
# query-mode options
@click.option("-c", "--code", metavar="CODE", help="The code snippet as a single string")
@click.option("--terminal", is_flag=True, help="Connect to the terminal-type compute_session.")
# batch-mode options
@click.option(
    "--clean", metavar="CMD", help="Custom shell command for cleaning up the base directory"
)
@click.option("--build", metavar="CMD", help="Custom shell command for building the given files")
@click.option("--exec", metavar="CMD", help="Custom shell command for executing the given files")
@click.option(
    "--basedir",
    metavar="PATH",
    type=click.Path(),
    default=None,
    help=(
        "Base directory path of uploaded files. "
        "All uploaded files must reside inside this directory."
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
    "--rm",
    is_flag=True,
    help="Terminate the session immediately after running the given code or files",
)
@click.option(
    "-s",
    "--stats",
    is_flag=True,
    help='Show resource usage statistics after termination (only works if "--rm" is given)',
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Hide execution details but show only the compute_session outputs.",
)
# experiment support
@click.option(
    "--env-range",
    metavar="RANGE_EXPR",
    multiple=True,
    type=range_expr,
    help="Range expression for environment variable.",
)
@click.option(
    "--build-range",
    metavar="RANGE_EXPR",
    multiple=True,
    type=range_expr,
    help="Range expression for execution arguments.",
)
@click.option(
    "--exec-range",
    metavar="RANGE_EXPR",
    multiple=True,
    type=range_expr,
    help="Range expression for execution arguments.",
)
@click.option(
    "--max-parallel",
    metavar="NUM",
    type=int,
    default=2,
    help="The maximum number of parallel sessions.",
)
# resource spec
@click.option(
    "--cluster-mode",
    metavar="MODE",
    type=click.Choice([*ClusterMode], case_sensitive=False),
    default=ClusterMode.SINGLE_NODE,
    help="The mode of clustering.",
)
@click.option(
    "--resource-opts",
    metavar="KEY=VAL",
    type=str,
    multiple=True,
    help="Resource options for creating compute session. (e.g: shmem=64m)",
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
# resource grouping
@click.option("--preopen", default=None, type=list_expr, help="Pre-open service ports")
@click.option(
    "--assign-agent",
    default=None,
    type=list_expr,
    help=(
        "Show mapping list of tuple which mapped containers with agent. "
        "When user role is Super Admin. "
        "(e.g., --assign-agent agent_id_1,agent_id_2,...)"
    ),
)
@click_start_option()
def run(
    image,
    files,
    name,  # click_start_option
    type,  # click_start_option
    starts_at,  # click_start_option
    enqueue_only,  # click_start_option
    max_wait,  # click_start_option
    no_reuse,  # click_start_option
    callback_url,  # click_start_option
    code,
    terminal,  # query-mode options
    clean,
    build,
    exec,
    basedir,  # batch-mode options
    env,  # click_start_option
    bootstrap_script,
    rm,
    stats,
    tag,  # click_start_option
    quiet,  # extra options
    env_range,
    build_range,
    exec_range,
    max_parallel,  # experiment support
    mount,  # click_start_option
    scaling_group,  # click_start_option
    resources,  # click_start_option
    cluster_size,  # click_start_option
    cluster_mode: ClusterMode,
    resource_opts,  # click_start_option
    architecture,
    domain,  # click_start_option
    group,  # click_start_option
    preopen,
    assign_agent,  # resource grouping
):
    """
    Run the given code snippet or files in a session.
    Depending on the session ID you give (default is random),
    it may reuse an existing session or create a new one.

    \b
    IMAGE: The name (and version/platform tags appended after a colon) of session
           runtime or programming language.
    FILES: The code file(s). Can be added multiple times.
    """
    if quiet:
        vprint_info = vprint_wait = vprint_done = _noop
    else:
        vprint_info = print_info
        vprint_wait = print_wait
        vprint_done = print_done
    if files and code:
        print("You can run only either source files or command-line code snippet.", file=sys.stderr)
        sys.exit(ExitCode.INVALID_ARGUMENT)
    if not files and not code:
        print(
            "You should provide the command-line code snippet using "
            '"-c" option if run without files.',
            file=sys.stderr,
        )
        sys.exit(ExitCode.INVALID_ARGUMENT)

    envs = prepare_env_arg(env)
    resources = prepare_resource_arg(resources)
    resource_opts = prepare_resource_arg(resource_opts)
    mount, mount_map, mount_options = prepare_mount_arg(mount, escape=True)

    if env_range is None:
        env_range = []  # noqa
    if build_range is None:
        build_range = []  # noqa
    if exec_range is None:
        exec_range = []  # noqa

    env_ranges = {v: r for v, r in env_range}
    build_ranges = {v: r for v, r in build_range}
    exec_ranges = {v: r for v, r in exec_range}

    env_var_maps = [
        dict(zip(env_ranges.keys(), values)) for values in itertools.product(*env_ranges.values())
    ]
    build_var_maps = [
        dict(zip(build_ranges.keys(), values))
        for values in itertools.product(*build_ranges.values())
    ]
    exec_var_maps = [
        dict(zip(exec_ranges.keys(), values)) for values in itertools.product(*exec_ranges.values())
    ]
    case_set = collections.OrderedDict()
    vmaps_product = itertools.product(env_var_maps, build_var_maps, exec_var_maps)
    build_template = string.Template(build)
    exec_template = string.Template(exec)
    env_templates = {k: string.Template(v) for k, v in envs.items()}

    if preopen is None:
        preopen = []  # noqa

    preopen_ports = preopen
    assigned_agent_list = assign_agent  # should be None if not specified
    for env_vmap, build_vmap, exec_vmap in vmaps_product:
        interpolated_envs = tuple((k, vt.substitute(env_vmap)) for k, vt in env_templates.items())
        if build:
            interpolated_build = build_template.substitute(build_vmap)
        else:
            interpolated_build = "*"
        if exec:
            interpolated_exec = exec_template.substitute(exec_vmap)
        else:
            interpolated_exec = "*"
        case_set[(interpolated_envs, interpolated_build, interpolated_exec)] = 1

    is_multi = len(case_set) > 1
    if is_multi:
        if max_parallel <= 0:
            print(
                "The number maximum parallel sessions must be a positive integer.",
                file=sys.stderr,
            )
            sys.exit(ExitCode.INVALID_ARGUMENT)
        if terminal:
            print("You cannot run multiple cases with terminal.", file=sys.stderr)
            sys.exit(ExitCode.INVALID_ARGUMENT)
        if not quiet:
            vprint_info("Running multiple sessions for the following combinations:")
            for case in case_set.keys():
                pretty_env = " ".join("{}={}".format(item[0], item[1]) for item in case[0])
                print("env = {!r}, build = {!r}, exec = {!r}".format(pretty_env, case[1], case[2]))

    def _run_legacy(session, idx, name, envs, clean_cmd, build_cmd, exec_cmd):
        try:
            compute_session = session.ComputeSession.get_or_create(
                image,
                name=name,
                type_=type,
                enqueue_only=enqueue_only,
                max_wait=max_wait,
                no_reuse=no_reuse,
                cluster_size=cluster_size,
                cluster_mode=cluster_mode,
                mounts=mount,
                mount_map=mount_map,
                envs=envs,
                resources=resources,
                domain_name=domain,
                group_name=group,
                scaling_group=scaling_group,
                tag=tag,
                architecture=architecture,
            )
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
        if compute_session.status == "PENDING":
            print_info("Session ID {0} is enqueued for scheduling.".format(name))
            return
        elif compute_session.status == "SCHEDULED":
            print_info("Session ID {0} is scheduled and about to be started.".format(name))
            return
        elif compute_session.status == "RUNNING":
            if compute_session.created:
                vprint_done(
                    "[{0}] Session {1} is ready (domain={2}, group={3}).".format(
                        idx, compute_session.name, compute_session.domain, compute_session.group
                    )
                )
            else:
                vprint_done("[{0}] Reusing session {1}...".format(idx, compute_session.name))
        elif compute_session.status == "TERMINATED":
            print_warn(
                "Session ID {0} is already terminated.\n"
                "This may be an error in the compute_session image.".format(name)
            )
            return
        elif compute_session.status == "TIMEOUT":
            print_info("Session ID {0} is still on the job queue.".format(name))
            return
        elif compute_session.status in ("ERROR", "CANCELLED"):
            print_fail(
                "Session ID {0} has an error during scheduling/startup or cancelled.".format(name)
            )
            return

        try:
            if files:
                vprint_wait("[{0}] Uploading source files...".format(idx))
                ret = compute_session.upload(files, basedir=basedir, show_progress=True)
                if ret.status // 100 != 2:
                    print_fail("[{0}] Uploading source files failed!".format(idx))
                    print("{0}: {1}\n{2}".format(ret.status, ret.reason, ret.text()))
                    return
                vprint_done("[{0}] Uploading done.".format(idx))
                opts = {
                    "clean": clean_cmd,
                    "build": build_cmd,
                    "exec": exec_cmd,
                }
                if not terminal:
                    exec_loop_sync(
                        sys.stdout,
                        sys.stderr,
                        compute_session,
                        "batch",
                        "",
                        opts=opts,
                        vprint_done=vprint_done,
                    )
            if terminal:
                raise NotImplementedError(
                    "Terminal access is not supported in the legacy synchronous mode."
                )
            if code:
                exec_loop_sync(
                    sys.stdout, sys.stderr, compute_session, "query", code, vprint_done=vprint_done
                )
            vprint_done("[{0}] Execution finished.".format(idx))
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
        finally:
            if rm:
                vprint_wait("[{0}] Cleaning up the session...".format(idx))
                ret = compute_session.destroy()
                vprint_done("[{0}] Cleaned up the session.".format(idx))
                if stats:
                    _stats = ret.get("stats", None) if ret else None
                    if _stats:
                        print("[{0}] Statistics:\n{1}".format(idx, format_stats(_stats)))
                    else:
                        print("[{0}] Statistics is not available.".format(idx))

    async def _run(session, idx, name, envs, clean_cmd, build_cmd, exec_cmd, is_multi=False):
        try:
            compute_session = await session.ComputeSession.get_or_create(
                image,
                name=name,
                type_=type,
                starts_at=starts_at,
                enqueue_only=enqueue_only,
                max_wait=max_wait,
                no_reuse=no_reuse,
                callback_url=callback_url,
                cluster_size=cluster_size,
                cluster_mode=cluster_mode,
                mounts=mount,
                mount_map=mount_map,
                mount_options=mount_options,
                envs=envs,
                resources=resources,
                resource_opts=resource_opts,
                domain_name=domain,
                group_name=group,
                scaling_group=scaling_group,
                bootstrap_script=bootstrap_script.read() if bootstrap_script is not None else None,
                tag=tag,
                architecture=architecture,
                preopen_ports=preopen_ports,
                assign_agent=assigned_agent_list,
            )
        except Exception as e:
            print_fail("[{0}] {1}".format(idx, e))
            return
        if compute_session.status == "PENDING":
            print_info("Session ID {0} is enqueued for scheduling.".format(name))
            return
        elif compute_session.status == "SCHEDULED":
            print_info("Session ID {0} is scheduled and about to be started.".format(name))
            return
        elif compute_session.status == "RUNNING":
            if compute_session.created:
                vprint_done(
                    "[{0}] Session {1} is ready (domain={2}, group={3}).".format(
                        idx, compute_session.name, compute_session.domain, compute_session.group
                    )
                )
            else:
                vprint_done("[{0}] Reusing session {1}...".format(idx, compute_session.name))
        elif compute_session.status == "TERMINATED":
            print_warn(
                "Session ID {0} is already terminated.\n"
                "This may be an error in the compute_session image.".format(name)
            )
            return
        elif compute_session.status == "TIMEOUT":
            print_info("Session ID {0} is still on the job queue.".format(name))
            return
        elif compute_session.status in ("ERROR", "CANCELLED"):
            print_fail(
                "Session ID {0} has an error during scheduling/startup or cancelled.".format(name)
            )
            return

        if not is_multi:
            stdout = sys.stdout
            stderr = sys.stderr
        else:
            log_dir = local_cache_path / "client-logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            stdout = open(log_dir / "{0}.stdout.log".format(name), "w", encoding="utf-8")
            stderr = open(log_dir / "{0}.stderr.log".format(name), "w", encoding="utf-8")

        try:

            def indexed_vprint_done(msg):
                vprint_done("[{0}] ".format(idx) + msg)

            if files:
                if not is_multi:
                    vprint_wait("[{0}] Uploading source files...".format(idx))
                ret = await compute_session.upload(
                    files, basedir=basedir, show_progress=not is_multi
                )
                if ret.status // 100 != 2:
                    print_fail("[{0}] Uploading source files failed!".format(idx))
                    print("{0}: {1}\n{2}".format(ret.status, ret.reason, ret.text()), file=stderr)
                    raise RuntimeError("Uploading source files has failed!")
                if not is_multi:
                    vprint_done("[{0}] Uploading done.".format(idx))
                opts = {
                    "clean": clean_cmd,
                    "build": build_cmd,
                    "exec": exec_cmd,
                }
                if not terminal:
                    await exec_loop(
                        stdout,
                        stderr,
                        compute_session,
                        "batch",
                        "",
                        opts=opts,
                        vprint_done=indexed_vprint_done,
                        is_multi=is_multi,
                    )
            if terminal:
                await exec_terminal(compute_session)
                return
            if code:
                await exec_loop(
                    stdout,
                    stderr,
                    compute_session,
                    "query",
                    code,
                    vprint_done=indexed_vprint_done,
                    is_multi=is_multi,
                )
        except BackendError as e:
            print_fail("[{0}] {1}".format(idx, e))
            raise RuntimeError(e)
        except Exception as e:
            print_fail("[{0}] Execution failed!".format(idx))
            traceback.print_exc()
            raise RuntimeError(e)
        finally:
            try:
                if rm:
                    if not is_multi:
                        vprint_wait("[{0}] Cleaning up the session...".format(idx))
                    ret = await compute_session.destroy()
                    vprint_done("[{0}] Cleaned up the session.".format(idx))
                    if stats:
                        _stats = ret.get("stats", None) if ret else None
                        if _stats:
                            stats_str = format_stats(_stats)
                            print(
                                format_info("[{0}] Statistics:".format(idx))
                                + "\n{0}".format(stats_str)
                            )
                            if is_multi:
                                print("Statistics:\n{0}".format(stats_str), file=stderr)
                        else:
                            print_warn("[{0}] Statistics: unavailable.".format(idx))
                            if is_multi:
                                print("Statistics: unavailable.", file=stderr)
            except Exception as e:
                print_fail("[{0}] Error while printing stats".format(idx))
                traceback.print_exc()
                raise RuntimeError(e)
            finally:
                if is_multi:
                    stdout.close()
                    stderr.close()

    async def _run_cases():
        loop = current_loop()
        if name is None:
            name_prefix = f"pysdk-{secrets.token_hex(5)}"
        else:
            name_prefix = name
        vprint_info("Session name prefix: {0}".format(name_prefix))
        if is_multi:
            print_info(
                "Check out the stdout/stderr logs stored in "
                "~/.cache/backend.ai/client-logs directory."
            )
        async with AsyncSession() as session:
            tasks = []
            # TODO: limit max-parallelism using aiojobs
            for idx, case in enumerate(case_set.keys()):
                if is_multi:
                    _name = "{0}-{1}".format(name_prefix, idx)
                else:
                    _name = name_prefix
                envs = dict(case[0])
                clean_cmd = clean if clean else "*"
                build_cmd = case[1]
                exec_cmd = case[2]
                t = loop.create_task(
                    _run(
                        session, idx, _name, envs, clean_cmd, build_cmd, exec_cmd, is_multi=is_multi
                    )
                )
                tasks.append(t)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            if any(map(lambda r: isinstance(r, Exception), results)):
                if is_multi:
                    print_fail("There were failed cases!")
                sys.exit(ExitCode.FAILURE)

    try:
        asyncio_run(_run_cases())
    except Exception as e:
        print_fail("{0}".format(e))
