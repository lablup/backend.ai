import ast
import configparser
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
        scan_entrypoint_from_plugin_checkouts(group_name),
        scan_entrypoint_from_package_metadata(group_name),
    ):
        if entrypoint.name in blocklist:
            continue
        if existing_entrypoint := existing_names.get(entrypoint.name, None):
            if existing_entrypoint.value == entrypoint.value:
                # Allow if the same plugin is scanned multiple times.
                # This may happen if:
                # - A plugin is installed via `./py -m pip install -e ...`
                # - The unified venv is re-exported *without* `./py -m pip uninstall ...`.
                # - Adding PYTHONPATH with plugin src directories in `./py` results in
                #   *duplicate* scan results from the remaining `.egg-info` directory (pkg metadata)
                #   and the `setup.cfg` scan results.
                # TODO: compare the plugin versions as well? (need to remember version with entrypoints)
                continue
            else:
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
    log.debug("scan_entrypoint_from_buildscript(%r): Namespace path: %s", group_name, ai_backend_ns_path)
    for buildscript_path in ai_backend_ns_path.glob("**/BUILD"):
        for entrypoint in extract_entrypoints_from_buildscript(group_name, buildscript_path):
            entrypoints[entrypoint.name] = entrypoint
    # Override with the entrypoints found in the current source directories,
    try:
        build_root = find_build_root()
    except ValueError:
        pass
    else:
        src_path = build_root / 'src'
        log.debug("scan_entrypoint_from_buildscript(%r): current src: %s", group_name, src_path)
        for buildscript_path in src_path.glob("**/BUILD"):
            for entrypoint in extract_entrypoints_from_buildscript(group_name, buildscript_path):
                entrypoints[entrypoint.name] = entrypoint
    yield from entrypoints.values()


def scan_entrypoint_from_plugin_checkouts(group_name: str) -> Iterator[EntryPoint]:
    entrypoints = {}
    try:
        build_root = find_build_root()
    except ValueError:
        pass
    else:
        plugins_path = build_root / 'plugins'
        log.debug("scan_entrypoint_from_plugin_checkouts(%r): plugin parent dir: %s", group_name, plugins_path)
        # For cases when plugins use Pants
        for buildscript_path in plugins_path.glob("**/BUILD"):
            for entrypoint in extract_entrypoints_from_buildscript(group_name, buildscript_path):
                entrypoints[entrypoint.name] = entrypoint
        # For cases when plugins use standard setup.cfg
        for setup_cfg_path in plugins_path.glob("**/setup.cfg"):
            for entrypoint in extract_entrypoints_from_setup_cfg(group_name, setup_cfg_path):
                if entrypoint.name not in entrypoints:
                    entrypoints[entrypoint.name] = entrypoint
        # TODO: implement pyproject.toml scanner
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


def extract_entrypoints_from_setup_cfg(
    group_name: str,
    setup_cfg_path: Path,
) -> Iterator[EntryPoint]:
    cfg = configparser.ConfigParser()
    cfg.read(setup_cfg_path)
    raw_data = cfg.get('options.entry_points', group_name, fallback="").strip()
    if not raw_data:
        return
    data = {
        k.strip(): v.strip()
        for k, v in (
            line.split("=", maxsplit=1)
            for line in
            raw_data.splitlines()
        )
    }
    for name, ref in data.items():
        yield EntryPoint(name=name, value=ref, group=group_name)
