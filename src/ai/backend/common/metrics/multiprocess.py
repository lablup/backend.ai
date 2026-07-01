"""
Prometheus multiprocess mode metric generation.

For directory setup, see ``multiprocess_setup.py`` — that module is kept
free of prometheus_client imports so the env var can be set before the
library determines its ValueClass.
"""

from __future__ import annotations

import logging
import os

from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client.multiprocess import MultiProcessCollector
from prometheus_client.multiprocess import mark_process_dead as _mark_dead

from ai.backend.common.metrics.multiprocess_setup import get_multiprocess_dir

log = logging.getLogger(__spec__.name)


def generate_latest_multiprocess() -> bytes:
    """
    Generate latest metrics aggregated across all worker processes.

    Always uses MultiProcessCollector to aggregate metrics from all workers
    that share the same PROMETHEUS_MULTIPROC_DIR.

    This should be used by multi-worker components (manager, agent, storage, etc.).
    """
    multiprocess_dir = get_multiprocess_dir()
    try:
        registry = CollectorRegistry()
        MultiProcessCollector(registry)  # type: ignore[no-untyped-call]
        return generate_latest(registry)
    except ValueError:
        # Directory may have been deleted (e.g., by systemd-tmpfiles-clean).
        # Attempt to recreate it and retry once.
        if multiprocess_dir is not None:
            try:
                multiprocess_dir.mkdir(parents=True, exist_ok=True)
                os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(multiprocess_dir)
                registry = CollectorRegistry()
                MultiProcessCollector(registry)  # type: ignore[no-untyped-call]
                log.warning(
                    "Prometheus multiprocess dir was missing and has been recreated: %s",
                    multiprocess_dir,
                )
                return generate_latest(registry)
            except Exception:
                log.error(
                    "Failed to recover prometheus multiprocess dir: %s",
                    multiprocess_dir,
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
