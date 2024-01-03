import sys
from pathlib import Path

import click
import humanize

from ai.backend.cli.main import main
from ai.backend.cli.params import (
    ByteSizeParamCheckType,
    ByteSizeParamType,
    CommaSeparatedKVListParamType,
)
from ai.backend.cli.types import ExitCode
from ai.backend.client.config import DEFAULT_CHUNK_SIZE, APIConfig
from ai.backend.client.output.fields import vfolder_fields
from ai.backend.client.session import Session

from ..exceptions import BackendAPIError
from ..output.types import FieldSpec
from .extensions import pass_ctx_obj
from .pretty import print_done
from .types import CLIContext


@main.group()
def model():
    """Set of model operations"""


@model.command()
@pass_ctx_obj
@click.option("--filter", "filter_", default=None, help="Set the query filter expression.")
@click.option("--order", default=None, help="Set the query ordering expression.")
@click.option("--offset", default=0, help="The index of the current page start for pagination.")
@click.option("--limit", type=int, default=None, help="The page size for pagination.")
def list(ctx: CLIContext, filter_, order, offset, limit):
    """
    List the models.
    """

    with Session() as session:
        try:
            fetch_func = lambda pg_offset, pg_size: session.Model.paginated_list(
                page_offset=pg_offset,
                page_size=pg_size,
                filter=filter_,
                order=order,
            )
            ctx.output.print_paginated_list(
                fetch_func,
                initial_page_offset=offset,
                page_size=limit,
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@model.command()
@pass_ctx_obj
@click.argument("model_name", metavar="MODEL", type=str)
def info(ctx: CLIContext, model_name):
    """
    Display the detail of a model with its backing storage vfolder.

    \b
    MODEL: The model name
    """

    with Session() as session:
        try:
            result = session.Model(model_name).info()
            ctx.output.print_item(
                result,
                [
                    vfolder_fields["id"],
                    vfolder_fields["name"],
                    FieldSpec("versions"),
                ],
            )
        except BackendAPIError as e:
            ctx.output.print_fail(
                "Not a valid model storage. "
                "There is no directory named `versions` under the model storage "
                "or model storage not found."
            )
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@model.command()
@pass_ctx_obj
@click.argument("name", type=str)
@click.argument("host", type=str, default=None)
@click.option(
    "-g",
    "--group",
    metavar="GROUP",
    type=str,
    default=None,
    help="Group ID or NAME.",
)
@click.option(
    "--unmanaged",
    "host_path",
    is_flag=True,
    help=(
        "Treats HOST as a mount point of unmanaged model. "
        "This option can only be used by Admin or Superadmin."
    ),
)
@click.option(
    "-p",
    "--permission",
    metavar="PERMISSION",
    type=str,
    default="rw",
    help=(
        "Folder's innate permission. "
        'Group folders can be shared as read-only by setting this option to "ro". '
        "Invited folders override this setting by its own invitation permission."
    ),
)
@click.option(
    "-q",
    "--quota",
    metavar="QUOTA",
    type=ByteSizeParamCheckType(),
    default="0",
    help=(
        "Quota of the virtual folder. "
        "(Use 'm' for megabytes, 'g' for gigabytes, and etc.) "
        "Default is maximum amount possible."
    ),
)
@click.option(
    "--cloneable",
    "--allow-clone",
    is_flag=True,
    help="Allows the virtual folder to be cloned by users.",
)
def create(ctx: CLIContext, name, host, group, host_path, permission, quota, cloneable):
    """
    Create a new model with the given configuration.

    \b
    NAME: Name of a model.
    HOST: Name of a virtual folder host in which the model will be created.
    """
    with Session() as session:
        try:
            if host_path:
                result = session.Model.create(
                    name=name,
                    host=host,
                    unmanaged_path=host_path,
                    group=group,
                    permission=permission,
                    quota=quota,
                    cloneable=cloneable,
                )
            else:
                result = session.Model.create(
                    name=name,
                    host=host,
                    group=group,
                    permission=permission,
                    quota=quota,
                    cloneable=cloneable,
                )
            print_done("Created the model.")
            ctx.output.print_item(result, [FieldSpec("id"), FieldSpec("name")])
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@model.command()
@pass_ctx_obj
@click.argument("model_name", metavar="MODEL", type=str)
def rm(ctx: CLIContext, model_name):
    """
    Remove the given model.

    \b
    MODEL: The model ID.
    """

    with Session() as session:
        try:
            serving = session.Model(model_name)
            serving.delete()
            print_done("Model deleted.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@model.command()
@pass_ctx_obj
@click.argument("model_name", metavar="MODEL", type=str)
@click.argument("filenames", type=Path, nargs=-1)
@click.argument("model_version", metavar="MODEL_VER", type=str)
@click.option(
    "-b",
    "--base-dir",
    type=Path,
    default=None,
    help=(
        "The local parent directory which contains the file to be uploaded.  "
        "[default: current working directry]"
    ),
)
@click.option(
    "--chunk-size",
    type=ByteSizeParamType(),
    default=humanize.naturalsize(DEFAULT_CHUNK_SIZE, binary=True, gnu=True),
    help=(
        'Transfer the file with the given chunk size with binary suffixes (e.g., "16m"). '
        "Set this between 8 to 64 megabytes for high-speed disks (e.g., SSD RAID) "
        "and networks (e.g., 40 GbE) for the maximum throughput."
    ),
)
@click.option(
    "--override-storage-proxy",
    type=CommaSeparatedKVListParamType(),
    default=None,
    help=(
        "Overrides storage proxy address. "
        'The value must shape like "X1=Y1,X2=Y2...". '
        "Each Yn address must at least include the IP address "
        "or the hostname and may include the protocol part and the port number to replace."
    ),
)
def upload(
    ctx: CLIContext,
    model_name,
    filenames,
    model_version,
    base_dir,
    chunk_size,
    override_storage_proxy,
):
    """
    Upload a file to the model as the given version.
    The files with the same names will be overwirtten.

    \b
    MODEL: The model ID
    FILENAMES: The uploaded files paths relative to the current working directory
    """
    with Session() as session:
        try:
            session.VFolder(model_name).upload(
                filenames,
                dst_dir=Path("versions", model_version),
                basedir=base_dir,
                chunk_size=chunk_size,
                show_progress=True,
                address_map=(
                    override_storage_proxy or APIConfig.DEFAULTS["storage_proxy_address_map"]
                ),
            )
            print_done("Done.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@model.command()
@pass_ctx_obj
@click.argument("model_name", type=str)
@click.argument("filenames", type=Path, nargs=-1)
@click.argument("model_version", metavar="MODEL_VER", type=str)
@click.option(
    "-b",
    "--base-dir",
    type=Path,
    default=None,
    help=(
        "The local parent directory which will contain the downloaded file.  "
        "[default: current working directry]"
    ),
)
@click.option(
    "--chunk-size",
    type=ByteSizeParamType(),
    default=humanize.naturalsize(DEFAULT_CHUNK_SIZE, binary=True, gnu=True),
    help=(
        'Transfer the file with the given chunk size with binary suffixes (e.g., "16m"). '
        "Set this between 8 to 64 megabytes for high-speed disks (e.g., SSD RAID) "
        "and networks (e.g., 40 GbE) for the maximum throughput."
    ),
)
@click.option(
    "--override-storage-proxy",
    type=CommaSeparatedKVListParamType(),
    default=None,
    help=(
        "Overrides storage proxy address. "
        'The value must shape like "X1=Y1,X2=Y2...". '
        "Each Yn address must at least include the IP address "
        "or the hostname and may include the protocol part and the port number to replace."
    ),
)
@click.option(
    "--max-retries",
    type=int,
    default=20,
    help="Maximum retry attempt when any failure occurs.",
)
def download(
    ctx: CLIContext,
    model_name,
    filenames,
    model_version,
    base_dir,
    chunk_size,
    override_storage_proxy,
    max_retries,
):
    """
    Download a file from the model storage.
    The files with the same names will be overwirtten.

    \b
    MODEL: The model ID
    FILENAMES: The file paths in the model storage vfolder to download to the current working
               directory.
    """
    with Session() as session:
        try:
            session.VFolder(model_name).download(
                filenames,
                dst_dir=Path("versions", model_version),
                basedir=base_dir,
                chunk_size=chunk_size,
                show_progress=True,
                address_map=(
                    override_storage_proxy or APIConfig.DEFAULTS["storage_proxy_address_map"]
                ),
                max_retries=max_retries,
            )
            print_done("Done.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
