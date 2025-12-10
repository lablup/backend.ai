"""
Lightweight entry point wrapper for the app-proxy-coordinator start-server command.

This module provides a minimal CLI entry point that defers heavy imports
until the command is actually executed, improving CLI startup time.
"""

from __future__ import annotations


def main() -> None:
    """
    Start the app-proxy coordinator service as a foreground process.

    This is a thin wrapper that defers the heavy import of server module.
    """
    from ai.backend.appproxy.coordinator.server import main as server_main

    server_main()
