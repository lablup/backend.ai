from __future__ import annotations

import asyncio
import logging
import subprocess
import sys
from datetime import datetime
from functools import partial
from pathlib import Path

import click
from more_itertools import chunked
from setproctitle import setproctitle

from ai.backend.cli.types import ExitCode
from ai.backend.common import redis_helper as redis_helper
from ai.backend.common.cli import LazyGroup
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.validators import TimeDuration

from ..config import load as load_config
from .context import CLIContext, init_logger, redis_ctx

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.cli"))


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=Path,
    default=None,
    help="The config file path. (default: ./manager.conf and /etc/backend.ai/manager.conf)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable the debug mode and override the global log level to DEBUG.",
)
@click.pass_context
def main(ctx, config_path, debug):
    """
    Manager Administration CLI
    """
    local_config = load_config(config_path)
    setproctitle(f"backend.ai: manager.cli {local_config['etcd']['namespace']}")
    ctx.obj = CLIContext(
        logger=init_logger(local_config),
        local_config=local_config,
    )


@main.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.option(
    "--psql-container",
    "container_name",
    type=str,
    default=None,
    metavar="ID_OR_NAME",
    help="Open a postgres client shell using the psql executable "
    "shipped with the given postgres container. "
    'If not set or set as an empty string "", it will auto-detect '
    "the psql container from the halfstack. "
    'If set "-", it will use the host-provided psql executable. '
    "You may append additional arguments passed to the psql cli command. "
    "[default: auto-detect from halfstack]",
)
@click.option(
    "--psql-help",
    is_flag=True,
    help="Show the help text of the psql command instead of " "this dbshell command.",
)
@click.argument("psql_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def dbshell(cli_ctx: CLIContext, container_name, psql_help, psql_args):
    """
    Run the database shell.

    All arguments except `--psql-container` and `--psql-help` are transparently
    forwarded to the psql command.  For instance, you can use `-c` to execute a
    psql/SQL statement on the command line.  Note that you do not have to specify
    connection-related options because the dbshell command fills out them from the
    manager configuration.
    """
    local_config = cli_ctx.local_config
    if psql_help:
        psql_args = ["--help"]
    if not container_name:
        # Try to get the database container name of the halfstack
        candidate_container_names = subprocess.check_output(
            ["docker", "ps", "--format", "{{.Names}}", "--filter", "name=half-db"],
        )
        if not candidate_container_names:
            click.echo(
                "Could not find the halfstack postgres container. "
                "Please set the container name explicitly.",
                err=True,
            )
            sys.exit(ExitCode.FAILURE)
        container_name = candidate_container_names.decode().splitlines()[0].strip()
    elif container_name == "-":
        # Use the host-provided psql command
        cmd = [
            "psql",
            (
                f"postgres://{local_config['db']['user']}:{local_config['db']['password']}"
                f"@{local_config['db']['addr']}/{local_config['db']['name']}"
            ),
            *psql_args,
        ]
        subprocess.call(cmd)
        return
    # Use the container to start the psql client command
    print(f"using the db container {container_name} ...")
    cmd = [
        "docker",
        "exec",
        "-i",
        "-t",
        container_name,
        "psql",
        "-U",
        local_config["db"]["user"],
        "-d",
        local_config["db"]["name"],
        *psql_args,
    ]
    subprocess.call(cmd)


@main.command()
@click.pass_obj
def generate_keypair(cli_ctx: CLIContext):
    """
    Generate a random keypair and print it out to stdout.
    """
    from ..models.keypair import generate_keypair as _gen_keypair

    log.info("generating keypair...")
    ak, sk = _gen_keypair()
    print(f"Access Key: {ak} ({len(ak)} bytes)")
    print(f"Secret Key: {sk} ({len(sk)} bytes)")


@main.command()
@click.option(
    "-r",
    "--retention",
    type=str,
    default="1yr",
    help="The retention limit. e.g., 20d, 1mo, 6mo, 1yr",
)
@click.option(
    "-v",
    "--vacuum-full",
    type=bool,
    default=False,
    help="Reclaim storage occupied by dead tuples."
    "If not set or set False, it will run VACUUM without FULL."
    "If set True, it will run VACUUM FULL."
    "When VACUUM FULL is being processed, the database is locked."
    "[default: False]",
)
@click.pass_obj
def clear_history(cli_ctx: CLIContext, retention, vacuum_full) -> None:
    """
    Delete old records from the kernels table and
    invoke the PostgreSQL's vaccuum operation to clear up the actual disk space.
    """
    import sqlalchemy as sa
    from redis.asyncio import Redis
    from redis.asyncio.client import Pipeline

    from ai.backend.manager.models import kernels
    from ai.backend.manager.models.utils import connect_database

    with cli_ctx.logger:
        today = datetime.now()
        duration = TimeDuration()
        expiration_date = today - duration.check_and_return(retention)

        async def _clear_redis_history():
            try:
                async with connect_database(cli_ctx.local_config) as db:
                    async with db.begin_readonly() as conn:
                        query = (
                            sa.select([kernels.c.id])
                            .select_from(kernels)
                            .where(
                                (kernels.c.terminated_at < expiration_date),
                            )
                        )
                        result = await conn.execute(query)
                        target_kernels = [str(x["id"]) for x in result.all()]

                delete_count = 0
                async with redis_ctx(cli_ctx) as redis_conn_set:

                    async def _build_pipe(
                        r: Redis,
                        kernel_ids: list[str],
                    ) -> Pipeline:
                        pipe = r.pipeline(transaction=False)
                        await pipe.delete(*kernel_ids)
                        return pipe

                    if len(target_kernels) > 0:
                        # Apply chunking to avoid excessive length of command params
                        # and indefinite blocking of the Redis server.
                        for kernel_ids in chunked(target_kernels, 32):
                            results = await redis_helper.execute(
                                redis_conn_set.stat,
                                partial(_build_pipe, kernel_ids=kernel_ids),
                            )
                        # Each DEL command returns the number of keys deleted.
                        delete_count += sum(results)
                        log.info(
                            "Cleaned up {:,} redis statistics records older than {:}.",
                            delete_count,
                            expiration_date,
                        )

                    # Sync and compact the persistent database of Redis
                    redis_config = await redis_helper.execute(
                        redis_conn_set.stat,
                        lambda r: r.config_get("appendonly"),
                    )
                    if redis_config["appendonly"] == "yes":
                        await redis_helper.execute(
                            redis_conn_set.stat,
                            lambda r: r.bgrewriteaof(),
                        )
                        log.info("Issued BGREWRITEAOF to the Redis database.")
                    else:
                        await redis_helper.execute(
                            redis_conn_set.stat,
                            lambda r: r.execute_command("BGSAVE SCHEDULE"),
                        )
                        log.info("Issued BGSAVE to the Redis database.")
            except Exception:
                log.exception("Unexpected error while cleaning up redis history")

        async def _clear_terminated_sessions():
            async with connect_database(cli_ctx.local_config, isolation_level="AUTOCOMMIT") as db:
                async with db.begin() as conn:
                    log.info("Deleting old records...")
                    result = await conn.execute(
                        sa.delete(kernels).where(kernels.c.terminated_at < expiration_date),
                    )
                    deleted_count = result.rowcount

                    vacuum_sql = "VACUUM FULL" if vacuum_full else "VACUUM"
                    log.info(f"Perfoming {vacuum_sql} operation...")
                    await conn.exec_driver_sql(vacuum_sql)

                    curs = await conn.execute(sa.select([sa.func.count()]).select_from(kernels))
                    if ret := curs.fetchone():
                        table_size = ret[0]
                        log.info(
                            "The number of rows of the `kernels` tables after cleanup: {}",
                            table_size,
                        )
            log.info(
                "Cleaned up {:,} database records older than {}.",
                deleted_count,
                expiration_date,
            )

        asyncio.run(_clear_redis_history())
        asyncio.run(_clear_terminated_sessions())


@main.group(cls=LazyGroup, import_name="ai.backend.manager.cli.dbschema:cli")
def schema():
    """Command set for managing the database schema."""


@main.group(cls=LazyGroup, import_name="ai.backend.manager.cli.etcd:cli")
def etcd():
    """Command set for putting/getting data to/from etcd."""


@main.group(cls=LazyGroup, import_name="ai.backend.manager.cli.fixture:cli")
def fixture():
    """Command set for managing fixtures."""


@main.group(cls=LazyGroup, import_name="ai.backend.manager.cli.gql:cli")
def gql():
    """Command set for GraphQL schema."""


@main.group(cls=LazyGroup, import_name="ai.backend.manager.cli.image:cli")
def image():
    """Command set for managing images."""


if __name__ == "__main__":
    main()
