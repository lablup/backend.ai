import ast
import logging
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import Container, Iterator

log = logging.getLogger(__name__)


def scan_entrypoints(
    group_name: str,
    blocklist: Container[str] = None,
) -> Iterator[EntryPoint]:
    if blocklist is None:
        blocklist = set()
    for entrypoint in scan_entrypoint_from_buildscript(group_name):
        if entrypoint.name in blocklist:
            continue
        yield entrypoint
    for entrypoint in scan_entrypoint_from_package_metadata(group_name):
        if entrypoint.name in blocklist:
            continue
        yield entrypoint


def scan_entrypoint_from_package_metadata(group_name: str) -> Iterator[EntryPoint]:
    for entrypoint in entry_points().get(group_name, []):
        yield entrypoint


def scan_entrypoint_from_buildscript(group_name: str) -> Iterator[EntryPoint]:
    ai_backend_ns_path = Path(__file__).parent.parent
    print("scan_entrypoint_from_buildscript(): Namespace path:", ai_backend_ns_path)
    print("scan_entrypoint_from_buildscript(): All BUILD files:\n", [*ai_backend_ns_path.glob("**/BUILD")])
    for buildscript_path in ai_backend_ns_path.glob("**/BUILD"):
        log.debug("reading entry points [{}] from {}", group_name, buildscript_path)
        yield from extract_entrypoints_from_buildscript(group_name, buildscript_path)


def extract_entrypoints_from_buildscript(
    group_name: str,
    buildscript_path: Path,
) -> Iterator[EntryPoint]:
    tree = ast.parse(buildscript_path.read_bytes())
    for node in tree.body:
        if (
            isinstance(node, ast.Expr) and
            isinstance(node.value, ast.Call) and
            isinstance(node.value.func, ast.Name) and
            node.value.func.id == "python_distribution"
        ):
            for kwarg in node.value.keywords:
                if kwarg.arg == "entry_points":
                    raw_data = ast.literal_eval(kwarg.value)
                    for key, raw_entry_points in raw_data.items():
                        if key != group_name:
                            continue
                        for name, ref in raw_entry_points.items():
                            try:
                                yield EntryPoint(name=name, value=ref, group=group_name)
                            except ValueError:
                                pass
