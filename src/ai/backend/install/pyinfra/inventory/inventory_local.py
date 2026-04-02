"""
Local development inventory for pyinfra CLI.

Usage:
    PYTHONPATH=src pyinfra inventory_local.py deploy/cores/appproxy/coordinator/deploy.py

This inventory uses @local connector (no SSH) and Docker Compose halfstack ports.
"""

from ai.backend.install.pyinfra.inventory.dev_inventory import DevInventoryBuilder

builder = DevInventoryBuilder()
locals().update(builder.build())
