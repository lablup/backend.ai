from typing import Sequence

import click

from ...session import Session
from ..pretty import print_error
from . import admin


@admin.group()
def resource() -> None:
    """
    Resource administration commands.
    """


@resource.command()
def query_slots() -> None:
    """
    Get available resource slots.
    """
    with Session() as session:
        try:
            ret = session.Resource.get_resource_slots()
            for key, value in ret.items():
                print(key, "(" + value + ")")
        except Exception as e:
            print_error(e)


@resource.command()
def vfolder_types() -> None:
    """
    Get available vfolder types.
    """
    with Session() as session:
        try:
            ret = session.Resource.get_vfolder_types()
            for t in ret:
                print(t)
        except Exception as e:
            print_error(e)


@resource.command()
def docker_registries() -> None:
    """
    Get registered docker registries.
    """
    with Session() as session:
        try:
            ret = session.Resource.get_docker_registries()
            for t in ret:
                print(t)
        except Exception as e:
            print_error(e)


@resource.command()
def recalculate_usage() -> None:
    """
    Re-calculate resource occupation by sessions.

    Sometime, reported allocated resources is deviated from the actual value.
    By executing this command, the discrepancy will be corrected with real value.
    """
    with Session() as session:
        try:
            session.Resource.recalculate_usage()
            print("Resource allocation is re-calculated.")
        except Exception as e:
            print_error(e)


@resource.command()
@click.argument("month", metavar="MONTH")
@click.argument("groups", metavar="GROUP_IDS", nargs=-1)
def usage_per_month(month: str, groups: Sequence[str]) -> None:
    """
    Get session usage stats of target groups for specific month.

    \b
    MONTH: Target month to get usage (yyyymm).
    GROUP_IDS: IDs of target groups to get usage (UUID).
    """
    with Session() as session:
        ret = session.Resource.usage_per_month(month, list(groups))
        for item in ret:
            print("Group:", item["g_name"] + " (" + item["g_id"] + ")")
            print("  Domain:", item["domain_name"])
            print(
                "  Total Allocated:",
                item["g_smp"],
                "core(s)",
                "/",
                item["g_mem_allocated"],
                "mem (bytes)",
            )
            print(
                "  Total CPU / Memory Used:",
                item["g_cpu_used"],
                "(s)",
                "/",
                item["g_mem_used"],
                "(bytes)",
            )
            print(
                "  Total I/O Read / Write:", item["g_io_read"], "/", item["g_io_write"], "(bytes)"
            )
            print("  GPU Devices:", item["g_device_type"])
            print("  Containers (" + str(len(item["c_infos"])) + "):")
            for cinfo in item["c_infos"]:
                print("    Identity:", cinfo["name"], "/", cinfo["access_key"])
                print("    Image:", cinfo["image_name"])
                print(
                    "    Duration:",
                    cinfo["used_days"],
                    "day(s)",
                    "(" + cinfo["created_at"] + " ~ " + cinfo["terminated_at"] + ")",
                )
                print(
                    "    Allocated:",
                    cinfo["smp"],
                    "core(s)",
                    "/",
                    cinfo["mem_allocated"],
                    "mem (bytes)",
                )
                print("    CPU / Memory Used:", cinfo["io_read"], "/", cinfo["io_write"], "(bytes)")
                print("    I/O Read / Write:", cinfo["io_read"], "/", cinfo["io_write"], "(bytes)")
                print("    NFS mounted:", cinfo["nfs"])
                print("    GPU Device:", cinfo["device_type"])
                print("    ----------------------------------------")
            print()


@resource.command()
@click.argument("group")
@click.argument("start_date")
@click.argument("end_date")
def usage_per_period(group: str, start_date: str, end_date: str) -> None:
    with Session() as session:
        item = session.Resource.usage_per_period(group, start_date, end_date)
        if "g_id" in item:
            print("Group:", item["g_name"] + " (" + item["g_id"] + ")")
            print("  Domain:", item["domain_name"])
            print(
                "  Total Allocated:",
                item["g_smp"],
                "core(s)",
                "/",
                item["g_mem_allocated"],
                "mem (bytes)",
            )
            print(
                "  Total CPU / Memory Used:",
                item["g_cpu_used"],
                "(s)",
                "/",
                item["g_mem_used"],
                "(bytes)",
            )
            print(
                "  Total I/O Read / Write:", item["g_io_read"], "/", item["g_io_write"], "(bytes)"
            )
            print("  GPU Devices:", item["g_device_type"])
            print("  Containers (" + str(len(item["c_infos"])) + "):")
            for cinfo in item["c_infos"]:
                print("    Identity:", cinfo["name"], "/", cinfo["access_key"])
                print("    Image:", cinfo["image_name"])
                print(
                    "    Duration:",
                    cinfo["used_days"],
                    "day(s)",
                    "(" + cinfo["created_at"] + " ~ " + cinfo["terminated_at"] + ")",
                )
                print(
                    "    Allocated:",
                    cinfo["smp"],
                    "core(s)",
                    "/",
                    cinfo["mem_allocated"],
                    "mem (bytes)",
                )
                print("    CPU / Memory Used:", cinfo["io_read"], "/", cinfo["io_write"], "(bytes)")
                print("    I/O Read / Write:", cinfo["io_read"], "/", cinfo["io_write"], "(bytes)")
                print("    NFS mounted:", cinfo["nfs"])
                print("    GPU Device:", cinfo["device_type"])
                print("    ----------------------------------------")
            print()
        else:
            print("No usage information during the period.")
