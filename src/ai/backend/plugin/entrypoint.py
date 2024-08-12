from __future__ import annotations

import ast
import collections
import configparser
import itertools
import logging
import os
import sys
import zipfile
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import Iterable, Iterator, Optional

log = logging.getLogger(__spec__.name)


def scan_entrypoints(
    group_name: str,
    allowlist: Optional[set[str]] = None,
    blocklist: Optional[set[str]] = None,
) -> Iterator[EntryPoint]:
    if blocklist is None:
        blocklist = set()
    existing_names: dict[str, EntryPoint] = {}

    prepare_wheelhouse()
    for entrypoint in itertools.chain(
        scan_entrypoint_from_buildscript(group_name),
        scan_entrypoint_from_package_metadata(group_name),
    ):
        if allowlist is not None and not match_plugin_list(entrypoint.value, allowlist):
            continue
        if match_plugin_list(entrypoint.value, blocklist):
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


def match_plugin_list(entry_path: str, plugin_list: set[str]) -> bool:
    """
    Checks if the given module attribute reference is in the plugin_list.
    The plugin_list items are assumeed to be prefixes of package import paths
    or the package namespaces.
    """
    mod_path = entry_path.partition(":")[0]
    for block_pattern in plugin_list:
        if mod_path.startswith(block_pattern + ".") or mod_path == block_pattern:
            return True
    return False


def scan_entrypoint_from_package_metadata(group_name: str) -> Iterator[EntryPoint]:
    log.debug("scan_entrypoint_from_package_metadata(%r)", group_name)

    yield from entry_points().select(group=group_name)


_default_glob_excluded_patterns = [
    "ai/backend/webui",
    "ai/backend/web/static",
    "ai/backend/runner",
    "ai/backend/kernel",
]


def _glob(base_path: Path, filename: str, excluded_patterns: Iterable[str]) -> Iterator[Path]:
    q: collections.deque[Path] = collections.deque()
    q.append(base_path)
    while q:
        search_path = q.pop()
        assert search_path.is_dir()
        for item in search_path.iterdir():
            if item.is_dir():
                if search_path.name == "__pycache__":
                    continue
                if search_path.name.startswith("."):
                    continue
                if any(search_path.match(pattern) for pattern in excluded_patterns):
                    continue
                q.append(item)
            else:
                if item.name == filename:
                    yield item


def scan_entrypoint_from_buildscript(group_name: str) -> Iterator[EntryPoint]:
    entrypoints = {}
    # Scan self-exported entrypoints when executed via pex.
    ai_backend_ns_path = Path(__file__).parent.parent
    log.debug(
        "scan_entrypoint_from_buildscript(%r): Namespace path: %s", group_name, ai_backend_ns_path
    )
    for buildscript_path in _glob(ai_backend_ns_path, "BUILD", _default_glob_excluded_patterns):
        for entrypoint in extract_entrypoints_from_buildscript(group_name, buildscript_path):
            entrypoints[entrypoint.name] = entrypoint
    # Override with the entrypoints found in the current source directories,
    try:
        build_root = find_build_root()
    except ValueError:
        pass
    else:
        src_path = build_root / "src"
        log.debug("scan_entrypoint_from_buildscript(%r): current src: %s", group_name, src_path)
        for buildscript_path in _glob(src_path, "BUILD", _default_glob_excluded_patterns):
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
        plugins_path = build_root / "plugins"
        log.debug(
            "scan_entrypoint_from_plugin_checkouts(%r): plugin parent dir: %s",
            group_name,
            plugins_path,
        )
        # For cases when plugins use Pants
        for buildscript_path in _glob(plugins_path, "BUILD", _default_glob_excluded_patterns):
            for entrypoint in extract_entrypoints_from_buildscript(group_name, buildscript_path):
                entrypoints[entrypoint.name] = entrypoint
        # For cases when plugins use standard setup.cfg
        for setup_cfg_path in _glob(plugins_path, "setup.cfg", _default_glob_excluded_patterns):
            for entrypoint in extract_entrypoints_from_setup_cfg(group_name, setup_cfg_path):
                if entrypoint.name not in entrypoints:
                    entrypoints[entrypoint.name] = entrypoint
        # TODO: implement pyproject.toml scanner
    yield from entrypoints.values()


def prepare_wheelhouse(base_dir: Path | None = None) -> None:
    if base_dir is None:
        base_dir = Path.cwd()
    for whl_path in (base_dir / "wheelhouse").glob("*.whl"):
        extracted_path = whl_path.with_suffix("")  # strip the extension
        log.debug("prepare_wheelhouse(): loading %s", whl_path)
        if not extracted_path.exists():
            with zipfile.ZipFile(whl_path, "r") as z:
                z.extractall(extracted_path)
        decoded_path = os.fsdecode(extracted_path)
        if decoded_path not in sys.path:
            sys.path.append(decoded_path)


def find_build_root(path: Optional[Path] = None) -> Path:
    if env_build_root := os.environ.get("BACKEND_BUILD_ROOT", None):
        return Path(env_build_root)
    cwd = Path.cwd() if path is None else path
    while True:
        if (cwd / "BUILD_ROOT").exists():
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
    try:
        tree = ast.parse(buildscript_path.read_bytes())
    except IsADirectoryError:
        # In macOS, "build" directories generated by build scripts of vendored repositories
        # are indistinguishable with "BUILD" files because macOS' default filesystem setting
        # ignores the cases of filenames.
        # Let's simply skip over in such cases.
        return
    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "python_distribution"
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
    raw_data = cfg.get("options.entry_points", group_name, fallback="").strip()
    if not raw_data:
        return
    data = {
        k.strip(): v.strip()
        for k, v in (line.split("=", maxsplit=1) for line in raw_data.splitlines())
    }
    for name, ref in data.items():
        yield EntryPoint(name=name, value=ref, group=group_name)
