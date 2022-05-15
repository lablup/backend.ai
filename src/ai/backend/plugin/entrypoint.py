import ast
import itertools
import logging
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import Container, Iterator, Optional

log = logging.getLogger(__name__)


def scan_entrypoints(
    group_name: str,
    blocklist: Container[str] = None,
) -> Iterator[EntryPoint]:
    if blocklist is None:
        blocklist = set()
    existing_names: dict[str, EntryPoint] = {}
    for entrypoint in itertools.chain(
        scan_entrypoint_from_buildscript(group_name),
        scan_entrypoint_from_package_metadata(group_name),
    ):
        if entrypoint.name in blocklist:
            continue
        if existing_entrypoint := existing_names.get(entrypoint.name):
            raise RuntimeError(
                f"Detected a duplicate plugin entrypoint name {entrypoint.name!r} "
                f"from {existing_entrypoint.value} and {entrypoint.value}",
            )
        existing_names[entrypoint.name] = entrypoint
        yield entrypoint


def scan_entrypoint_from_package_metadata(group_name: str) -> Iterator[EntryPoint]:
    yield from entry_points().select(group=group_name)


def scan_entrypoint_from_buildscript(group_name: str) -> Iterator[EntryPoint]:
    entrypoints = {}
    # Scan self-exported entrypoints when executed via pex.
    ai_backend_ns_path = Path(__file__).parent.parent
    log.debug("scan_entrypoint_from_buildscript({!r}): Namespace path: {}", group_name, ai_backend_ns_path)
    for buildscript_path in ai_backend_ns_path.glob("**/BUILD"):
        log.debug("reading entry points [{}] from {}", group_name, buildscript_path)
        for entrypoint in extract_entrypoints_from_buildscript(group_name, buildscript_path):
            entrypoints[entrypoint.name] = entrypoint
    # Override with the entrypoints found in the current source directories,
    try:
        build_root = find_build_root()
    except ValueError:
        pass
    else:
        src_path = build_root / 'src'
        plugins_path = build_root / 'plugins'
        log.debug("scan_entrypoint_from_buildscript({!r}): current src: {}", group_name, src_path)
        for buildscript_path in src_path.glob("**/BUILD"):
            if buildscript_path.is_relative_to(plugins_path):
                # Prevent loading BUILD files in plugin checkouts if they use Pants on their own.
                continue
            log.debug("reading entry points [{}] from {}", group_name, buildscript_path)
            for entrypoint in extract_entrypoints_from_buildscript(group_name, buildscript_path):
                entrypoints[entrypoint.name] = entrypoint
    yield from entrypoints.values()


def find_build_root(path: Optional[Path] = None) -> Path:
    cwd = Path.cwd() if path is None else path
    while True:
        if (cwd / 'BUILD_ROOT').exists():
            return cwd
        cwd = cwd.parent
        if cwd.parent == cwd:
            # reached the root directory
            break
    raise ValueError("Could not find the build root directory")


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
