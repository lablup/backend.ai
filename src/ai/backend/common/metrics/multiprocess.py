"""
Prometheus multiprocess mode support.

In multiprocess environments (e.g., manager with multiple workers via aiotools),
each worker process has its own prometheus_client registry. Without multiprocess mode,
Prometheus scraping via a shared port (reuse_port=True) only sees one random worker's
metrics per scrape, leading to incorrect counter values.

This module provides:
- setup_prometheus_multiprocess_dir(): Must be called BEFORE any prometheus_client import
- generate_latest_multiprocess(): Always aggregates metrics across all workers
- generate_latest_singleprocess(): For single-process components using default registry
- cleanup_prometheus_multiprocess_dir(): Called on full server shutdown
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client.multiprocess import MultiProcessCollector
from prometheus_client.multiprocess import mark_process_dead as _mark_dead

log = logging.getLogger(__spec__.name)

_multiprocess_dir: Path | None = None

_DEFAULT_BASE_DIR = Path("/var/run/backendai/prometheus/")


def setup_prometheus_multiprocess_dir(
    component: str = "manager",
) -> Path:
    """
    Set up the prometheus multiprocess directory and environment variable.

    MUST be called before any prometheus_client import.

    Creates a directory for prometheus multiprocess files and sets
    the PROMETHEUS_MULTIPROC_DIR environment variable.

    Args:
        component: Component name for directory naming (e.g., 'manager', 'agent')

    Returns:
        Path to the created multiprocess directory
    """
    global _multiprocess_dir

    if _multiprocess_dir is not None:
        return _multiprocess_dir

    multiprocess_dir = _DEFAULT_BASE_DIR / component
    multiprocess_dir.mkdir(parents=True, exist_ok=True)

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


def generate_latest_multiprocess() -> bytes:
    """
    Generate latest metrics aggregated across all worker processes.

    Always uses MultiProcessCollector to aggregate metrics from all workers
    that share the same PROMETHEUS_MULTIPROC_DIR.

    This should be used by multi-worker components (manager, agent, storage, etc.).
    """
    try:
        registry = CollectorRegistry()
        MultiProcessCollector(registry)  # type: ignore[no-untyped-call]
        return generate_latest(registry)
    except ValueError:
        # Directory may have been deleted (e.g., by systemd-tmpfiles-clean).
        # Attempt to recreate it and retry once.
        if _multiprocess_dir is not None:
            try:
                _multiprocess_dir.mkdir(parents=True, exist_ok=True)
                os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(_multiprocess_dir)
                registry = CollectorRegistry()
                MultiProcessCollector(registry)  # type: ignore[no-untyped-call]
                log.warning(
                    "Prometheus multiprocess dir was missing and has been recreated: %s",
                    _multiprocess_dir,
                )
                return generate_latest(registry)
            except Exception:
                log.error(
                    "Failed to recover prometheus multiprocess dir: %s",
                    _multiprocess_dir,
                    exc_info=True,
                )
        return b""


def generate_latest_singleprocess() -> bytes:
    """
    Generate latest metrics from the default process-local registry.

    This should be used by single-process components that do not need
    multiprocess aggregation.
    """
    return generate_latest()


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


def mark_process_dead(pid: int) -> None:
    """
    Mark a worker process as dead for prometheus multiprocess cleanup.

    Should be called when a worker process exits to clean up its metric files.

    Args:
        pid: Process ID of the dead worker
    """
    try:
        _mark_dead(pid)  # type: ignore[no-untyped-call]
    except Exception:
        log.debug("Failed to mark process %d as dead for prometheus", pid, exc_info=True)
