"""
Prometheus multiprocess directory setup.

This module intentionally does NOT import prometheus_client so that it can
be safely imported and called before any prometheus_client import.

prometheus_client determines its ValueClass (MutexValue vs MmapedValue) at
import time by checking the PROMETHEUS_MULTIPROC_DIR environment variable.
Once fixed, it never re-evaluates — even across fork().  Keeping this module
free of prometheus_client ensures the env var is set before the library loads.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

log = logging.getLogger(__spec__.name)

_multiprocess_dir: Path | None = None

_DEFAULT_BASE_DIR = Path("./run/prometheus")


def setup_prometheus_multiprocess_dir(
    component: str = "manager",
    base_dir: Path | None = None,
) -> Path:
    """
    Set up the prometheus multiprocess directory and environment variable.

    MUST be called before any prometheus_client import.

    Creates a directory for prometheus multiprocess files and sets
    the PROMETHEUS_MULTIPROC_DIR environment variable.

    The base directory is resolved in the following priority order:
    1. ``base_dir`` argument (if provided)
    2. ``BACKENDAI_PROMETHEUS_DIR`` environment variable (if set)
    3. Default: ``./run/prometheus/``

    Args:
        component: Component name for directory naming (e.g., 'manager', 'agent')
        base_dir: Optional override for the base directory. Takes precedence over
            the ``BACKENDAI_PROMETHEUS_DIR`` environment variable.

    Returns:
        Path to the created multiprocess directory
    """
    global _multiprocess_dir

    if _multiprocess_dir is not None:
        return _multiprocess_dir

    if base_dir is not None:
        resolved_base = base_dir
    elif env_base := os.environ.get("BACKENDAI_PROMETHEUS_DIR"):
        resolved_base = Path(env_base)
    else:
        resolved_base = _DEFAULT_BASE_DIR

    multiprocess_dir = resolved_base / component
    try:
        multiprocess_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        log.error(
            "Cannot create prometheus multiprocess dir %s — permission denied. "
            "Ensure the directory is writable by the current user.",
            multiprocess_dir,
        )
        raise

    # Clean stale .db files from previous runs
    for db_file in multiprocess_dir.glob("*.db"):
        try:
            db_file.unlink()
        except OSError:
            pass

    os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(multiprocess_dir)
    _multiprocess_dir = multiprocess_dir
    log.info("Prometheus multiprocess dir: %s", multiprocess_dir)
    return multiprocess_dir


def cleanup_prometheus_multiprocess_dir() -> None:
    """
    Clean up the prometheus multiprocess directory.

    Should be called on full server shutdown (not per-worker).
    """
    global _multiprocess_dir

    if _multiprocess_dir is not None and _multiprocess_dir.exists():
        shutil.rmtree(_multiprocess_dir, ignore_errors=True)
        log.info("Cleaned up prometheus multiprocess dir: %s", _multiprocess_dir)
        _multiprocess_dir = None

    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        del os.environ["PROMETHEUS_MULTIPROC_DIR"]


def get_multiprocess_dir() -> Path | None:
    """Return the current multiprocess directory, if configured."""
    return _multiprocess_dir
